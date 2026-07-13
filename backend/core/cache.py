"""Simple in-memory TTL cache for expensive queries."""
import time
from typing import Any, Callable

_cache: dict[str, tuple[float, Any]] = {}
DEFAULT_TTL = 60  # seconds


def get_cached(key: str, ttl: int = DEFAULT_TTL) -> Any | None:
    """Get a cached value if it exists and hasn't expired."""
    if key in _cache:
        ts, val = _cache[key]
        if time.time() - ts < ttl:
            return val
        del _cache[key]
    return None


def set_cached(key: str, value: Any) -> None:
    """Store a value in cache with current timestamp."""
    _cache[key] = (time.time(), value)


def cached_call(key: str, fn: Callable, ttl: int = DEFAULT_TTL) -> Any:
    """Call fn() if cache miss, return cached value otherwise."""
    val = get_cached(key, ttl)
    if val is not None:
        return val
    val = fn()
    set_cached(key, val)
    return val


def invalidate(key: str | None = None) -> None:
    """Invalidate a specific key or clear all."""
    if key:
        _cache.pop(key, None)
    else:
        _cache.clear()
