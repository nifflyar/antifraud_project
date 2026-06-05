import hashlib
import json
from functools import wraps
from typing import Any, Callable, TypeVar
import asyncio

from app.infrastructure.cache import get_cache

T = TypeVar("T")

_dedup_cache: dict[str, asyncio.Future] = {}


def cache_result(ttl: int = 60, cache_key_fn: Callable | None = None):
    """
    Decorator for caching async function results with TTL.
    Also deduplicates concurrent identical requests (waits for first result).
    """

    def decorator(func: Callable[..., Any]) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = await get_cache()
            if not cache:
                return await func(*args, **kwargs)

            if cache_key_fn:
                cache_key = cache_key_fn(**kwargs)
            else:
                key_data = json.dumps(
                    {"fn": func.__name__, "args": str(args), "kwargs": str(kwargs)},
                    default=str,
                    sort_keys=True,
                )
                cache_key = hashlib.md5(key_data.encode()).hexdigest()

            cached = await cache.get(cache_key)
            if cached:
                return cached

            dedup_key = f"{func.__name__}:{cache_key}"
            if dedup_key in _dedup_cache:
                return await _dedup_cache[dedup_key]

            future = asyncio.Future()
            _dedup_cache[dedup_key] = future

            try:
                result = await func(*args, **kwargs)
                await cache.set(cache_key, result, ttl=ttl)
                future.set_result(result)
                return result
            except Exception as e:
                future.set_exception(e)
                raise
            finally:
                _dedup_cache.pop(dedup_key, None)

        return wrapper

    return decorator
