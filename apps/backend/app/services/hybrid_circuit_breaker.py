"""
Hybrid Circuit Breaker (MongoDB-Backed + Local Cache)

Implements circuit breaker pattern with:
- Local cache for fast state checks
- MongoDB for distributed state coordination
- Automatic recovery after cooldown

States:
- CLOSED: Normal operation
- OPEN: Supplier degraded, blocking requests
- HALF_OPEN: Testing recovery

Collection: supplier_circuit
Document structure:
{
  "_id": "amadeus",
  "state": "OPEN",
  "opened_at": 1702896234,
  "retry_after": 300,
  "failure_count": 3,
  "last_error": "429",
  "updated_at": ISODate(...)
}
"""

import time
import logging
from typing import Optional, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

# Configuration
TRIP_THRESHOLD = 3  # Failures before opening circuit
COOLDOWN_SECONDS = 300  # 5 minutes

class HybridCircuitBreaker:
    """
    MongoDB-backed circuit breaker with local caching.
    
    Uses local cache to minimize DB calls for common operations.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["supplier_circuit"]
        
        # Local cache: {supplier: (state, opened_at, last_check_time)}
        self.local_cache = {}
        self.cache_ttl = 10  # seconds
        
        # Local failure tracking
        self.local_failures = {}
        
        logger.info("HybridCircuitBreaker initialized")
    
    async def ensure_indexes(self):
        """Create indexes."""
        try:
            await self.collection.create_index("state", background=True)
            logger.info("Circuit breaker indexes created")
        except Exception as e:
            logger.warning(f"Failed to create indexes: {e}")
    
    async def is_open(self, supplier: str) -> Tuple[bool, dict]:
        """
        Check if circuit is open (blocking requests).
        
        Returns:
            (is_open: bool, metadata: dict)
        """
        now = time.time()
        
        # Check local cache first
        if supplier in self.local_cache:
            state, opened_at, cached_at = self.local_cache[supplier]
            
            # Use cache if fresh
            if now - cached_at < self.cache_ttl:
                if state == "OPEN":
                    elapsed = now - opened_at
                    if elapsed >= COOLDOWN_SECONDS:
                        # Cooldown elapsed - transition to HALF_OPEN
                        self.local_cache[supplier] = ("HALF_OPEN", opened_at, now)
                        await self._write_state_db(supplier, "HALF_OPEN", opened_at)
                        return False, {"state": "HALF_OPEN", "reason": "cooldown_elapsed"}
                    
                    return True, {
                        "state": "OPEN",
                        "opened_at": opened_at,
                        "retry_after_seconds": COOLDOWN_SECONDS - elapsed
                    }
                
                return False, {"state": state}
        
        # Cache miss or stale - read from DB
        try:
            doc = await self.collection.find_one({"_id": supplier})
            
            if doc:
                state = doc.get("state", "CLOSED")
                opened_at = doc.get("opened_at", 0)
                
                self.local_cache[supplier] = (state, opened_at, now)
                
                if state == "OPEN":
                    elapsed = now - opened_at
                    if elapsed >= COOLDOWN_SECONDS:
                        # Transition to HALF_OPEN
                        self.local_cache[supplier] = ("HALF_OPEN", opened_at, now)
                        await self._write_state_db(supplier, "HALF_OPEN", opened_at)
                        return False, {"state": "HALF_OPEN"}
                    
                    return True, {
                        "state": "OPEN",
                        "opened_at": opened_at,
                        "retry_after_seconds": COOLDOWN_SECONDS - elapsed
                    }
            
            # No document = CLOSED
            self.local_cache[supplier] = ("CLOSED", 0, now)
            return False, {"state": "CLOSED"}
            
        except Exception as e:
            logger.exception(f"DB error checking circuit: {e}")
            # Fail open if DB is down
            return False, {"state": "unknown", "error": "db_unavailable"}
    
    async def on_success(self, supplier: str):
        """Record successful request."""
        self.local_failures[supplier] = 0
        
        # If was HALF_OPEN or OPEN, close circuit
        if supplier in self.local_cache:
            state = self.local_cache[supplier][0]
            if state in ["HALF_OPEN", "OPEN"]:
                now = time.time()
                self.local_cache[supplier] = ("CLOSED", 0, now)
                await self._write_state_db(supplier, "CLOSED", None)
                logger.info(f"✅ Circuit breaker {supplier}: {state} → CLOSED (recovered)")
    
    async def on_failure(self, supplier: str, error_code: str):
        """Record failed request."""
        failures = self.local_failures.get(supplier, 0) + 1
        self.local_failures[supplier] = failures
        
        logger.warning(
            f"⚠️  Failure recorded for {supplier}: {failures}/{TRIP_THRESHOLD} (error: {error_code})"
        )
        
        # Check if should trip
        if failures >= TRIP_THRESHOLD:
            opened_at = int(time.time())
            now = time.time()
            
            self.local_cache[supplier] = ("OPEN", opened_at, now)
            await self._write_state_db(supplier, "OPEN", opened_at, error_code)
            
            logger.error(
                f"🚫 Circuit breaker {supplier}: CLOSED → OPEN "
                f"(failures: {failures}, error: {error_code})"
            )
    
    async def _write_state_db(self, supplier: str, state: str, opened_at: Optional[int], last_error: Optional[str] = None):
        """Write circuit state to MongoDB."""
        try:
            update_doc = {
                "state": state,
                "updated_at": time.time()
            }
            
            if opened_at is not None:
                update_doc["opened_at"] = opened_at
                update_doc["retry_after"] = COOLDOWN_SECONDS
            
            if last_error:
                update_doc["last_error"] = last_error
                update_doc["failure_count"] = self.local_failures.get(supplier, 0)
            
            await self.collection.update_one(
                {"_id": supplier},
                {"$set": update_doc},
                upsert=True
            )
        except Exception as e:
            logger.error(f"Error writing circuit state: {e}")
    
    async def get_status(self, supplier: str) -> dict:
        """Get circuit breaker status."""
        try:
            doc = await self.collection.find_one({"_id": supplier})
            
            if doc:
                state = doc.get("state", "CLOSED")
                opened_at = doc.get("opened_at", 0)
                
                result = {
                    "supplier": supplier,
                    "state": state,
                    "failure_count": doc.get("failure_count", 0),
                    "failure_threshold": TRIP_THRESHOLD,
                    "last_error": doc.get("last_error"),
                    "cooldown_seconds": COOLDOWN_SECONDS
                }
                
                if state == "OPEN" and opened_at > 0:
                    elapsed = time.time() - opened_at
                    result["opened_at"] = opened_at
                    result["retry_after_seconds"] = max(0, COOLDOWN_SECONDS - elapsed)
                
                return result
            
            return {
                "supplier": supplier,
                "state": "CLOSED",
                "failure_count": 0
            }
            
        except Exception as e:
            logger.error(f"Error getting circuit status: {e}")
            return {"error": str(e)}
    
    async def reset(self, supplier: str):
        """Reset circuit breaker (testing/admin use)."""
        self.local_failures[supplier] = 0
        self.local_cache.pop(supplier, None)
        
        try:
            await self.collection.update_one(
                {"_id": supplier},
                {"$set": {"state": "CLOSED", "failure_count": 0}}
            )
            logger.info(f"Reset circuit breaker for {supplier}")
        except Exception as e:
            logger.error(f"Error resetting circuit: {e}")
