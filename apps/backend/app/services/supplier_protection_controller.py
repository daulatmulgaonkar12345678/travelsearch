"""
Supplier Protection Controller (Hybrid System)

Glue layer that coordinates:
1. Local token buckets (fast, in-memory)
2. Global quota store (MongoDB, per-minute)
3. Circuit breaker (MongoDB + local cache)

Fail-Safe Behavior:
- If MongoDB is unreachable, instances fail-open with WARNING
- Local rate limiting still enforced for basic protection
- Logs heavily when in degraded mode
"""

import logging
import asyncio
from typing import Tuple, Dict, Optional

from app.services.local_rate_limiter import LocalTokenBucket
from app.services.global_quota_store import GlobalQuotaStore
from app.services.hybrid_circuit_breaker import HybridCircuitBreaker
from app.db.mongodb import get_database

logger = logging.getLogger(__name__)

# Supplier Configuration
SUPPLIER_CONFIG = {
    "amadeus": {
        "rps": 3.0,
        "burst": 5.0,
        "per_minute": 100,
        "enabled": True
    },
    "flightapi": {
        "rps": 3.0,
        "burst": 5.0,
        "per_minute": 200,
        "enabled": True
    },
    "duffel": {
        "rps": 2.0,
        "burst": 3.0,
        "per_minute": 100,
        "enabled": False
    },
    "kiwi": {
        "rps": 2.0,
        "burst": 3.0,
        "per_minute": 150,
        "enabled": False
    }
}

class SupplierProtectionController:
    """
    Central controller for supplier protection.
    
    Coordinates local rate limiting, global quotas, and circuit breaking.
    """
    
    def __init__(self):
        self.initialized = False
        self.local_buckets = {}
        self.global_quota = None
        self.circuit_breaker = None
        
        # Metrics
        self.metrics = {
            "total_requests": 0,
            "allowed": 0,
            "blocked_local_rate": 0,
            "blocked_global_quota": 0,
            "blocked_circuit_open": 0,
            "db_unavailable_count": 0
        }
    
    async def initialize(self):
        """Initialize protection components."""
        if self.initialized:
            return
        
        try:
            # Get MongoDB database
            db = await get_database()
            
            # Initialize components
            self.global_quota = GlobalQuotaStore(db)
            self.circuit_breaker = HybridCircuitBreaker(db)
            
            # Create indexes
            await self.global_quota.ensure_indexes()
            await self.circuit_breaker.ensure_indexes()
            
            # Initialize local token buckets
            for supplier, config in SUPPLIER_CONFIG.items():
                if config.get("enabled", True):
                    self.local_buckets[supplier] = LocalTokenBucket(
                        rate_per_sec=config["rps"],
                        burst=config["burst"]
                    )
            
            self.initialized = True
            logger.info("✅ SupplierProtectionController initialized (Hybrid Mode)")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize SupplierProtectionController: {e}")
            # Don't raise - allow system to start in degraded mode
    
    async def allow_request(
        self,
        supplier: str,
        queue_timeout: float = 0.3
    ) -> Tuple[bool, str, Dict]:
        """
        Check if request should be allowed.
        
        Returns:
            (allowed: bool, reason: str, metadata: dict)
            
        Reasons:
            - "allowed" - request permitted
            - "circuit_open" - circuit breaker is open
            - "local_rate_exceeded" - local RPS limit hit
            - "global_quota_exhausted" - per-minute quota exhausted
            - "db_unavailable_fail_open" - DB down, allowing with warning
            - "supplier_not_configured" - unknown supplier
        """
        self.metrics["total_requests"] += 1
        
        # Check if supplier is configured
        if supplier not in SUPPLIER_CONFIG:
            logger.warning(f"Supplier {supplier} not configured - allowing")
            return True, "supplier_not_configured", {}
        
        config = SUPPLIER_CONFIG[supplier]
        
        # Check if supplier is enabled
        if not config.get("enabled", True):
            return False, "supplier_disabled", {}
        
        # Step 1: Check circuit breaker
        if self.circuit_breaker:
            try:
                is_open, circuit_meta = await self.circuit_breaker.is_open(supplier)
                
                if is_open:
                    self.metrics["blocked_circuit_open"] += 1
                    logger.warning(
                        f"🚫 {supplier} blocked: circuit_open "
                        f"(retry_after: {circuit_meta.get('retry_after_seconds', 0):.0f}s)"
                    )
                    return False, "circuit_open", circuit_meta
            except Exception as e:
                logger.exception(f"Circuit breaker check failed: {e}")
                # Continue despite error
        
        # Step 2: Local rate limiting (token bucket)
        bucket = self.local_buckets.get(supplier)
        if not bucket:
            # Create on-demand if missing
            bucket = LocalTokenBucket(config["rps"], config["burst"])
            self.local_buckets[supplier] = bucket
        
        local_ok = bucket.wait_consume(tokens=1.0, timeout=queue_timeout)
        
        if not local_ok:
            self.metrics["blocked_local_rate"] += 1
            logger.warning(f"⏸️  {supplier} blocked: local_rate_exceeded")
            return False, "local_rate_exceeded", bucket.peek()
        
        # Step 3: Global quota check (per-minute)
        if self.global_quota:
            try:
                allowed_per_min = config["per_minute"]
                global_ok = await self.global_quota.try_increment(supplier, allowed_per_min)
                
                if not global_ok:
                    self.metrics["blocked_global_quota"] += 1
                    logger.warning(f"⛔ {supplier} blocked: global_quota_exhausted")
                    
                    # Get current quota status
                    status = await self.global_quota.get_status(supplier)
                    return False, "global_quota_exhausted", status or {}
            
            except Exception as e:
                logger.exception(f"⚠️  DB unavailable: fail-open for {supplier}")
                self.metrics["db_unavailable_count"] += 1
                # Fail open but log heavily
                return True, "db_unavailable_fail_open", {"warning": "db_error"}
        
        # All checks passed
        self.metrics["allowed"] += 1
        return True, "allowed", {}
    
    async def on_supplier_success(self, supplier: str):
        """Record successful supplier response."""
        if self.circuit_breaker:
            try:
                await self.circuit_breaker.on_success(supplier)
            except Exception as e:
                logger.error(f"Error recording success: {e}")
    
    async def on_supplier_failure(self, supplier: str, error_code: str):
        """Record failed supplier response."""
        if self.circuit_breaker:
            try:
                await self.circuit_breaker.on_failure(supplier, error_code)
            except Exception as e:
                logger.error(f"Error recording failure: {e}")
    
    async def get_status(self, supplier: str) -> Dict:
        """Get comprehensive status for a supplier."""
        status = {
            "supplier": supplier,
            "configured": supplier in SUPPLIER_CONFIG
        }
        
        if supplier in SUPPLIER_CONFIG:
            config = SUPPLIER_CONFIG[supplier]
            status["config"] = config
            
            # Local bucket status
            bucket = self.local_buckets.get(supplier)
            if bucket:
                status["local_bucket"] = bucket.peek()
            
            # Global quota status
            if self.global_quota:
                try:
                    quota_status = await self.global_quota.get_status(supplier)
                    if quota_status:
                        status["global_quota"] = quota_status
                except Exception as e:
                    status["global_quota"] = {"error": str(e)}
            
            # Circuit breaker status
            if self.circuit_breaker:
                try:
                    circuit_status = await self.circuit_breaker.get_status(supplier)
                    status["circuit_breaker"] = circuit_status
                except Exception as e:
                    status["circuit_breaker"] = {"error": str(e)}
        
        return status
    
    def get_metrics(self) -> Dict:
        """Get aggregated metrics."""
        return {
            **self.metrics,
            "block_rate": (
                (self.metrics["blocked_local_rate"] + 
                 self.metrics["blocked_global_quota"] + 
                 self.metrics["blocked_circuit_open"]) / 
                max(1, self.metrics["total_requests"])
            ) * 100
        }

# Global singleton instance
_controller: Optional[SupplierProtectionController] = None

async def get_controller() -> SupplierProtectionController:
    """Get or create the global controller instance."""
    global _controller
    
    if _controller is None:
        _controller = SupplierProtectionController()
        await _controller.initialize()
    
    return _controller

# Convenience functions
async def allow_request(supplier: str, queue_timeout: float = 0.3) -> Tuple[bool, str, Dict]:
    """Check if request is allowed."""
    controller = await get_controller()
    return await controller.allow_request(supplier, queue_timeout)

async def on_supplier_success(supplier: str):
    """Record successful response."""
    controller = await get_controller()
    await controller.on_supplier_success(supplier)

async def on_supplier_failure(supplier: str, error_code: str):
    """Record failed response."""
    controller = await get_controller()
    await controller.on_supplier_failure(supplier, error_code)

async def get_supplier_status(supplier: str) -> Dict:
    """Get supplier status."""
    controller = await get_controller()
    return await controller.get_status(supplier)

async def get_metrics() -> Dict:
    """Get metrics."""
    controller = await get_controller()
    return controller.get_metrics()
