from typing import Any, Optional
import json
import asyncio
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class CacheService:
    """In-memory cache with Redis-compatible interface"""
    
    def __init__(self):
        # In-memory cache for development
        # Replace with Redis client in production
        self._cache = {}
        self._expiry = {}
        self.redis_available = False
        
        # Try to connect to Redis if available
        try:
            # from redis import asyncio as aioredis
            # self.redis = aioredis.from_url(settings.redis_url)
            # self.redis_available = True
            pass
        except Exception as e:
            logger.warning(f"Redis not available, using in-memory cache: {e}")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if self.redis_available:
            # return await self.redis.get(key)
            pass
        
        # In-memory cache
        if key in self._cache:
            # Check expiry
            if key in self._expiry and datetime.utcnow() > self._expiry[key]:
                del self._cache[key]
                del self._expiry[key]
                return None
            return self._cache[key]
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 900):
        """Set value in cache with TTL in seconds"""
        if self.redis_available:
            # await self.redis.setex(key, ttl, json.dumps(value))
            pass
        
        # In-memory cache
        self._cache[key] = value
        self._expiry[key] = datetime.utcnow() + timedelta(seconds=ttl)
    
    async def delete(self, key: str):
        """Delete key from cache"""
        if self.redis_available:
            # await self.redis.delete(key)
            pass
        
        if key in self._cache:
            del self._cache[key]
        if key in self._expiry:
            del self._expiry[key]
    
    async def clear(self):
        """Clear all cache"""
        if self.redis_available:
            # await self.redis.flushdb()
            pass
        
        self._cache.clear()
        self._expiry.clear()
