"""
Redis Client Singleton

Provides a centralized Redis connection for:
- Rate limiting (token bucket)
- Circuit breaker state
- Caching
- Pub/sub for events
"""

import redis.asyncio as aioredis
import logging
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)

class RedisClient:
    """Singleton Redis client with connection pooling."""
    
    _instance: Optional['RedisClient'] = None
    _redis: Optional[aioredis.Redis] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def connect(self):
        """Establish Redis connection."""
        if self._redis is None:
            try:
                redis_url = getattr(settings, 'redis_url', 'redis://redis:6379/0')
                self._redis = await aioredis.from_url(
                    redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    max_connections=50
                )
                # Test connection
                await self._redis.ping()
                logger.info(f"✅ Redis connected: {redis_url}")
            except Exception as e:
                logger.error(f"❌ Redis connection failed: {e}")
                self._redis = None
    
    async def disconnect(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None
            logger.info("Redis disconnected")
    
    def get_client(self) -> Optional[aioredis.Redis]:
        """Get Redis client instance."""
        return self._redis
    
    async def health_check(self) -> bool:
        """Check if Redis is healthy."""
        try:
            if self._redis:
                await self._redis.ping()
                return True
        except:
            pass
        return False

# Global Redis client instance
redis_client = RedisClient()
