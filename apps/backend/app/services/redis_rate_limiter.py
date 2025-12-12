"""
Redis-Based Token Bucket Rate Limiter

Implements a distributed token bucket algorithm using Redis and Lua scripts.
Prevents 429 errors by enforcing RPS/RPM limits globally across all instances.

Features:
- Atomic token consumption via Lua
- Burst capacity with gradual refill
- Request queuing with timeout
- Prometheus metrics
"""

import time
import asyncio
import logging
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Lua script for atomic token bucket operation
TOKEN_BUCKET_LUA = """
local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local refill_per_sec = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local tokens_requested = tonumber(ARGV[4])

local data = redis.call("HMGET", key, "tokens", "last_refill")
local tokens = tonumber(data[1]) or capacity
local last_refill = tonumber(data[2]) or now

-- Calculate tokens to add based on time elapsed
local delta = math.max(0, now - last_refill)
local tokens_to_add = delta * refill_per_sec
tokens = math.min(capacity, tokens + tokens_to_add)

-- Try to consume tokens
if tokens >= tokens_requested then
    tokens = tokens - tokens_requested
    redis.call("HMSET", key, "tokens", tokens, "last_refill", now)
    redis.call("EXPIRE", key, 120)  -- 2 minute TTL
    return {1, tokens}  -- allowed=1, remaining=tokens
else
    redis.call("HMSET", key, "tokens", tokens, "last_refill", now)
    redis.call("EXPIRE", key, 120)
    return {0, tokens}  -- allowed=0, remaining=tokens
end
"""

@dataclass
class RateLimitConfig:
    """Rate limit configuration for a supplier."""
    supplier_id: str
    requests_per_second: int = 3
    requests_per_minute: int = 100
    burst_capacity: int = 5
    queue_timeout_ms: int = 2000

class RedisRateLimiter:
    """
    Distributed rate limiter using Redis token bucket.
    
    Ensures global rate limiting across all backend instances.
    """
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.configs: Dict[str, RateLimitConfig] = {}
        self._lua_script_sha: Optional[str] = None
        
        # Metrics
        self.metrics = {
            "allowed_total": 0,
            "blocked_total": 0,
            "queued_total": 0,
            "queue_time_ms_total": 0,
        }
    
    async def initialize(self):
        """Load Lua script into Redis."""
        try:
            client = self.redis.get_client()
            if client:
                self._lua_script_sha = await client.script_load(TOKEN_BUCKET_LUA)
                logger.info("✅ Rate limiter Lua script loaded")
        except Exception as e:
            logger.error(f"Failed to load Lua script: {e}")
    
    def configure(self, config: RateLimitConfig):
        """Configure rate limits for a supplier."""
        self.configs[config.supplier_id] = config
        logger.info(
            f"⚙️  Rate limiter configured for {config.supplier_id}: "
            f"{config.requests_per_second} RPS, {config.requests_per_minute} RPM, "
            f"burst={config.burst_capacity}"
        )
    
    async def acquire(self, supplier_id: str) -> Tuple[bool, Dict]:
        """
        Acquire permission to make a request.
        
        Returns:
            (allowed: bool, metadata: dict)
        """
        if supplier_id not in self.configs:
            # No rate limiting configured
            return True, {"reason": "no_config"}
        
        config = self.configs[supplier_id]
        client = self.redis.get_client()
        
        if not client:
            logger.warning("Redis unavailable - allowing request (degraded mode)")
            return True, {"reason": "redis_unavailable"}
        
        # Try to acquire token
        start_time = time.time()
        allowed, remaining = await self._try_acquire(client, config)
        
        if allowed:
            self.metrics["allowed_total"] += 1
            return True, {
                "remaining": remaining,
                "wait_ms": 0
            }
        
        # Token not available - queue with timeout
        logger.warning(
            f"⏸️  Rate limit reached for {supplier_id}. "
            f"Remaining tokens: {remaining}. Queueing..."
        )
        self.metrics["queued_total"] += 1
        
        # Poll with exponential backoff
        attempts = 0
        max_attempts = config.queue_timeout_ms // 200  # Poll every 200ms
        
        while attempts < max_attempts:
            await asyncio.sleep(0.2)  # 200ms
            attempts += 1
            
            allowed, remaining = await self._try_acquire(client, config)
            if allowed:
                elapsed_ms = (time.time() - start_time) * 1000
                self.metrics["queue_time_ms_total"] += elapsed_ms
                self.metrics["allowed_total"] += 1
                logger.info(f"⏳ Request queued for {elapsed_ms:.0f}ms, then allowed")
                return True, {
                    "remaining": remaining,
                    "wait_ms": elapsed_ms
                }
        
        # Timeout - reject request
        elapsed_ms = (time.time() - start_time) * 1000
        logger.error(
            f"❌ Rate limit timeout for {supplier_id} after {elapsed_ms:.0f}ms. "
            f"Request blocked."
        )
        self.metrics["blocked_total"] += 1
        return False, {
            "reason": "rate_limited",
            "wait_ms": elapsed_ms
        }
    
    async def _try_acquire(self, client, config: RateLimitConfig) -> Tuple[bool, int]:
        """Attempt to acquire a token atomically."""
        try:
            key = f"rate:{config.supplier_id}:global"
            now = time.time()
            
            # Execute Lua script
            result = await client.evalsha(
                self._lua_script_sha,
                1,  # Number of keys
                key,
                config.burst_capacity,
                config.requests_per_second,
                now,
                1  # tokens requested
            )
            
            allowed = bool(result[0])
            remaining = int(result[1])
            return allowed, remaining
            
        except Exception as e:
            logger.error(f"Token bucket error: {e}")
            # Fail open in case of Redis errors
            return True, 0
    
    async def get_status(self, supplier_id: str) -> Dict:
        """Get current rate limiter status for a supplier."""
        if supplier_id not in self.configs:
            return {"error": "not_configured"}
        
        config = self.configs[supplier_id]
        client = self.redis.get_client()
        
        if not client:
            return {"error": "redis_unavailable"}
        
        try:
            key = f"rate:{supplier_id}:global"
            data = await client.hmget(key, "tokens", "last_refill")
            
            tokens = float(data[0]) if data[0] else config.burst_capacity
            last_refill = float(data[1]) if data[1] else time.time()
            
            return {
                "supplier_id": supplier_id,
                "capacity": config.burst_capacity,
                "current_tokens": round(tokens, 2),
                "refill_per_sec": config.requests_per_second,
                "last_refill_ago_ms": round((time.time() - last_refill) * 1000, 2),
                "queue_timeout_ms": config.queue_timeout_ms
            }
        except Exception as e:
            logger.error(f"Error getting rate limiter status: {e}")
            return {"error": str(e)}
    
    def get_metrics(self) -> Dict:
        """Get aggregated metrics."""
        return {
            **self.metrics,
            "avg_queue_time_ms": (
                self.metrics["queue_time_ms_total"] / self.metrics["queued_total"]
                if self.metrics["queued_total"] > 0
                else 0
            )
        }
