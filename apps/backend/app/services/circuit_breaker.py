"""
Circuit Breaker for Supplier Health Management

Tracks supplier health and temporarily disables unhealthy suppliers.
"""

import time
from typing import Dict, Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)

@dataclass
class SupplierHealth:
    """Track health metrics for a supplier."""
    supplier_id: str
    consecutive_failures: int = 0
    last_failure_time: float = 0
    circuit_open_until: float = 0
    total_calls: int = 0
    total_failures: int = 0
    
class CircuitBreaker:
    """
    Circuit breaker pattern implementation for supplier health.
    
    Rules:
    - After 3 consecutive 5xx/timeout errors, open circuit for 5 minutes
    - During circuit open, skip supplier entirely
    - After circuit closes, allow requests again
    """
    
    def __init__(
        self,
        failure_threshold: int = 3,
        circuit_open_seconds: int = 300  # 5 minutes
    ):
        self.failure_threshold = failure_threshold
        self.circuit_open_seconds = circuit_open_seconds
        self.suppliers: Dict[str, SupplierHealth] = {}
        
    def record_success(self, supplier_id: str):
        """Record a successful call."""
        if supplier_id not in self.suppliers:
            self.suppliers[supplier_id] = SupplierHealth(supplier_id=supplier_id)
        
        health = self.suppliers[supplier_id]
        health.consecutive_failures = 0
        health.total_calls += 1
        
    def record_failure(self, supplier_id: str, error_type: str = "5xx"):
        """Record a failed call."""
        if supplier_id not in self.suppliers:
            self.suppliers[supplier_id] = SupplierHealth(supplier_id=supplier_id)
        
        health = self.suppliers[supplier_id]
        health.consecutive_failures += 1
        health.total_failures += 1
        health.total_calls += 1
        health.last_failure_time = time.time()
        
        # Open circuit if threshold reached
        if health.consecutive_failures >= self.failure_threshold:
            health.circuit_open_until = time.time() + self.circuit_open_seconds
            logger.warning(
                f"🚫 Circuit breaker OPENED for {supplier_id} "
                f"after {health.consecutive_failures} failures. "
                f"Will retry in {self.circuit_open_seconds}s"
            )
    
    def is_available(self, supplier_id: str) -> bool:
        """Check if supplier is available (circuit closed)."""
        if supplier_id not in self.suppliers:
            return True
        
        health = self.suppliers[supplier_id]
        
        # Check if circuit is open
        if time.time() < health.circuit_open_until:
            return False
        
        # Check 429 count from rate limiter
        from app.services.rate_limiter import rate_limiter
        recent_429s = rate_limiter.get_429_count_last_minute(supplier_id)
        
        # Open circuit if too many 429s (3+ in last minute)
        if recent_429s >= 3:
            health.circuit_open_until = time.time() + self.circuit_open_seconds
            logger.warning(
                f"🚫 Circuit breaker OPENED for {supplier_id} due to {recent_429s} "
                f"429 errors in last minute. Will retry in {self.circuit_open_seconds}s"
            )
            return False
        
        # Circuit was open but time has passed - reset
        if health.circuit_open_until > 0:
            logger.info(f"✅ Circuit breaker CLOSED for {supplier_id} - retrying")
            health.consecutive_failures = 0
            health.circuit_open_until = 0
        
        return True
    
    def get_health(self, supplier_id: str) -> Optional[SupplierHealth]:
        """Get health metrics for a supplier."""
        return self.suppliers.get(supplier_id)
    
    def get_stats(self) -> Dict:
        """Get overall circuit breaker statistics."""
        return {
            supplier_id: {
                "total_calls": health.total_calls,
                "total_failures": health.total_failures,
                "consecutive_failures": health.consecutive_failures,
                "circuit_open": time.time() < health.circuit_open_until,
                "failure_rate": health.total_failures / health.total_calls if health.total_calls > 0 else 0
            }
            for supplier_id, health in self.suppliers.items()
        }

# Global circuit breaker instance
circuit_breaker = CircuitBreaker()
