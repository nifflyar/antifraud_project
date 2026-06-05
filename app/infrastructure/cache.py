"""Redis caching layer for high-performance queries."""
import json
import os
import redis.asyncio as redis
from datetime import datetime, timedelta
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)


class CacheManager:
    """Redis cache with TTL support for dashboards and list endpoints."""

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_url = redis_url
        self.client: Optional[redis.Redis] = None
        self.default_ttl = 300  # 5 minutes for dashboards

    async def connect(self):
        """Initialize Redis connection."""
        try:
            self.client = await redis.from_url(self.redis_url, decode_responses=True)
            await self.client.ping()
            logger.info("✅ Redis connected")
        except Exception as e:
            logger.warning(f"⚠️ Redis unavailable: {e} - falling back to no cache")
            self.client = None

    async def get(self, key: str) -> Optional[dict]:
        """Get value from cache."""
        if not self.client:
            return None
        try:
            val = await self.client.get(key)
            if val:
                return json.loads(val)
        except Exception as e:
            logger.warning(f"Cache GET error: {e}")
        return None

    async def set(self, key: str, value: dict, ttl: int = 300) -> bool:
        """Set value in cache with TTL."""
        if not self.client:
            return False
        try:
            await self.client.setex(key, ttl, json.dumps(value))
            return True
        except Exception as e:
            logger.warning(f"Cache SET error: {e}")
        return False

    async def delete(self, key: str) -> bool:
        """Delete from cache."""
        if not self.client:
            return False
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Cache DELETE error: {e}")
        return False

    async def flush_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        if not self.client:
            return 0
        try:
            keys = await self.client.keys(pattern)
            if keys:
                return await self.client.delete(*keys)
        except Exception as e:
            logger.warning(f"Cache FLUSH error: {e}")
        return 0

    @staticmethod
    def make_key(*parts) -> str:
        """Create cache key from parts."""
        return ":".join(str(p) for p in parts)


# Global cache instance
_cache: Optional[CacheManager] = None


async def get_cache() -> CacheManager:
    """Get or initialize cache."""
    global _cache
    if _cache is None:
        _cache = CacheManager(os.environ.get("REDIS_URL", "redis://localhost:6379/0"))
        await _cache.connect()
    return _cache
