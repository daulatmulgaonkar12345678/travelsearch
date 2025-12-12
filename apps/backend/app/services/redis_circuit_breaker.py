"""
Redis-Based Circuit Breaker

Distributed circuit breaker pattern for supplier health management.
Prevents cascading failures by temporarily disabling unhealthy suppliers.

States:
- CLOSED: Normal operation (all requests allowed)
- OPEN: Supplier degraded (all requests blocked)
- HALF_OPEN: Testing recovery (single probe request)

Triggers:
- 429 (rate limit)
- 401 (auth failure) 
- 5xx (server errors)
- Timeouts
"""

import time
import logging
from typing import Dict, Optional
from enum import Enum

logger = logging.getLogger(__name__)

class CircuitState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

class RedisCircuitBreaker:
    """
    Distributed circuit breaker using Redis for state coordination.
    
    Ensures all backend instances respect the same circuit state.
    """
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.configs = {}  # supplier_id -> config
        
        # Metrics
        self.metrics = {
            "failures_total": 0,
            "circuit_open_count": 0,
            "probes_total": 0,
            "probes_success": 0
        }
    
    def configure(self, supplier_id: str, failure_threshold: int = 3, cooldown_seconds: int = 300):
        """Configure circuit breaker for a supplier."""
        self.configs[supplier_id] = {
            "failure_threshold": failure_threshold,
            "cooldown_seconds": cooldown_seconds
        }
        logger.info(
            f"⚙️  Circuit breaker configured for {supplier_id}: "
            f"threshold={failure_threshold}, cooldown={cooldown_seconds}s"
        )
    
    async def is_available(self, supplier_id: str) -> Tuple[bool, Dict]:
        """
        Check if supplier is available (circuit closed or half-open).
        
        Returns:
            (available: bool, metadata: dict)
        """
        if supplier_id not in self.configs:
            # No circuit breaker configured
            return True, {"state": "no_config"}
        
        client = self.redis.get_client()
        if not client:
            logger.warning("Redis unavailable - allowing request (degraded mode)")
            return True, {"state": "redis_unavailable"}
        
        try:
            key = f"circuit:{supplier_id}"
            data = await client.hgetall(key)
            
            if not data:
                # No circuit data - default to CLOSED
                return True, {"state": CircuitState.CLOSED}
            
            state = data.get("state", CircuitState.CLOSED)
            failures = int(data.get("failures", 0))
            opened_at = float(data.get("opened_at", 0))
            
            if state == CircuitState.CLOSED:
                return True, {"state": CircuitState.CLOSED, "failures": failures}
            
            if state == CircuitState.OPEN:
                # Check if cooldown has elapsed
                config = self.configs[supplier_id]
                elapsed = time.time() - opened_at
                
                if elapsed >= config["cooldown_seconds"]:
                    # Transition to HALF_OPEN
                    await client.hset(key, "state", CircuitState.HALF_OPEN)
                    logger.info(f"🔗 Circuit breaker {supplier_id}: OPEN → HALF_OPEN (testing)")
                    return True, {"state": CircuitState.HALF_OPEN, "probe": True}
                else:
                    retry_after = config["cooldown_seconds"] - elapsed
                    return False, {
                        "state": CircuitState.OPEN,
                        "retry_after_seconds": round(retry_after, 2),
                        "opened_at": opened_at
                    }
            
            if state == CircuitState.HALF_OPEN:
                # Allow probe request
                return True, {"state": CircuitState.HALF_OPEN, "probe": True}
            
            return True, {"state": state}
            
        except Exception as e:
            logger.error(f"Circuit breaker check error: {e}")
            # Fail open
            return True, {"error": str(e)}
    
    async def record_success(self, supplier_id: str):
        """Record a successful request."""
        if supplier_id not in self.configs:
            return
        
        client = self.redis.get_client()
        if not client:
            return
        
        try:
            key = f"circuit:{supplier_id}"
            data = await client.hgetall(key)
            
            if not data:
                return
            
            state = data.get("state", CircuitState.CLOSED)
            
            if state == CircuitState.HALF_OPEN:
                # Probe succeeded - close circuit
                await client.hset(key, mapping={
                    "state": CircuitState.CLOSED,
                    "failures": 0,
                    "opened_at": 0
                })
                logger.info(f"✅ Circuit breaker {supplier_id}: HALF_OPEN → CLOSED (recovered)")
                self.metrics["probes_success"] += 1
            elif state == CircuitState.CLOSED:
                # Reset failure count on success
                await client.hset(key, "failures", 0)
            
        except Exception as e:
            logger.error(f"Error recording success: {e}")
    
    async def record_failure(self, supplier_id: str, error_code: str):
        """
        Record a failed request.
        
        Args:
            supplier_id: Supplier identifier
            error_code: Error type (429, 401, 5xx, timeout)
        """
        if supplier_id not in self.configs:
            return
        
        client = self.redis.get_client()
        if not client:
            return
        
        try:
            key = f"circuit:{supplier_id}"
            config = self.configs[supplier_id]
            
            # Get current state
            data = await client.hgetall(key)
            state = data.get("state", CircuitState.CLOSED) if data else CircuitState.CLOSED
            failures = int(data.get("failures", 0)) if data else 0
            
            if state == CircuitState.HALF_OPEN:
                # Probe failed - reopen circuit
                await client.hset(key, mapping={
                    "state": CircuitState.OPEN,
                    "failures": failures + 1,
                    "opened_at": time.time(),
                    "last_error": error_code
                })
                await client.expire(key, config["cooldown_seconds"] + 60)
                logger.warning(f"🚫 Circuit breaker {supplier_id}: HALF_OPEN → OPEN (probe failed: {error_code})")
                self.metrics["circuit_open_count"] += 1
                self.metrics["probes_total"] += 1
                return
            
            # Increment failures
            failures += 1
            self.metrics["failures_total"] += 1
            
            # Check threshold
            if failures >= config["failure_threshold"]:
                # Open circuit
                await client.hset(key, mapping={
                    "state": CircuitState.OPEN,
                    "failures": failures,
                    "opened_at": time.time(),
                    "last_error": error_code
                })
                await client.expire(key, config["cooldown_seconds"] + 60)
                
                logger.warning(
                    f"🚫 Circuit breaker {supplier_id}: CLOSED → OPEN "
                    f"(failures: {failures}/{config['failure_threshold']}, error: {error_code})"
                )
                self.metrics["circuit_open_count"] += 1
                
                # Send alert (if configured)
                await self._send_alert(supplier_id, error_code, failures)
            else:
                # Just increment failure count
                await client.hset(key, "failures", failures)
                await client.hset(key, "last_error", error_code)
                logger.warning(
                    f"⚠️  Failure recorded for {supplier_id}: {failures}/{config['failure_threshold']} (error: {error_code})"
                )
        
        except Exception as e:
            logger.error(f"Error recording failure: {e}")
    
    async def _send_alert(self, supplier_id: str, error_code: str, failures: int):
        """Send alert when circuit opens (webhook to Slack/PagerDuty)."""
        try:
            from app.config import settings
            import httpx
            
            # Mock webhook for now
            webhook_url = getattr(settings, 'mock_slack_webhook', None)
            
            if webhook_url and webhook_url != "https://example.com/mock-slack":
                message = {
                    "text": f"🚨 Circuit Breaker Alert",
                    "blocks": [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": (
                                    f"*Supplier*: {supplier_id}\n"
                                    f"*Status*: Circuit OPEN\n"
                                    f"*Error*: {error_code}\n"
                                    f"*Failures*: {failures}\n"
                                    f"*Action*: Using fallback providers"
                                )
                            }
                        }
                    ]
                }
                
                async with httpx.AsyncClient(timeout=5.0) as client:
                    await client.post(webhook_url, json=message)
                    logger.info(f"📨 Alert sent for {supplier_id}")
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")
    
    async def get_status(self, supplier_id: str) -> Dict:
        """Get current circuit breaker status."""
        if supplier_id not in self.configs:
            return {"error": "not_configured"}
        
        client = self.redis.get_client()
        if not client:
            return {"error": "redis_unavailable"}
        
        try:
            key = f"circuit:{supplier_id}"
            data = await client.hgetall(key)
            
            if not data:
                return {
                    "supplier_id": supplier_id,
                    "state": CircuitState.CLOSED,
                    "failures": 0
                }
            
            state = data.get("state", CircuitState.CLOSED)
            failures = int(data.get("failures", 0))
            opened_at = float(data.get("opened_at", 0))
            last_error = data.get("last_error", None)
            
            result = {
                "supplier_id": supplier_id,
                "state": state,
                "failures": failures,
                "failure_threshold": self.configs[supplier_id]["failure_threshold"],
                "last_error": last_error
            }
            
            if state == CircuitState.OPEN and opened_at > 0:
                config = self.configs[supplier_id]
                elapsed = time.time() - opened_at
                retry_after = max(0, config["cooldown_seconds"] - elapsed)
                result["opened_at"] = opened_at
                result["retry_after_seconds"] = round(retry_after, 2)
            
            return result
        
        except Exception as e:
            logger.error(f"Error getting circuit status: {e}")
            return {"error": str(e)}
    
    def get_metrics(self) -> Dict:
        """Get aggregated metrics."""
        return self.metrics

from typing import Tuple
