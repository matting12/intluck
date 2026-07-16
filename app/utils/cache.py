__all__ = [
    'get_cached',
    'set_cached',
    'clear_cache',
    'get_cache_stats',
    'ONE_HOUR',
    'ONE_DAY',
    'SEVEN_DAYS'
]

import os
import time
import hashlib
import json
from typing import Any

# Set CACHE_ENABLED=true in .env to enable caching
_CACHE_ENABLED = os.getenv("CACHE_ENABLED", "false").lower() != "false"

# In-memory cache storage
_cache: dict[str, dict] = {}

# TTL constants
ONE_HOUR = 3600
ONE_DAY = 86400
SEVEN_DAYS = 604800


def _make_key(prefix: str, params: dict) -> str:
    """Generate cache key from prefix and params"""
    print(params)
    param_str = json.dumps(params, sort_keys=True)
    hash_str = hashlib.md5(param_str.encode()).hexdigest()[:12]
    return f"{prefix}:{hash_str}"


def get_cached(prefix: str, params: dict) -> Any | None:
    """Caching is temporarily disabled for all callers — always returns None."""
    return None


def set_cached(prefix: str, params: dict, value: Any, ttl: int = ONE_DAY) -> None:
    """Caching is temporarily disabled for all callers — no-op."""
    return


def clear_cache() -> None:
    """Clear all cached entries"""
    _cache.clear()


def get_cache_stats() -> dict:
    """Return cache statistics for debugging"""
    now = time.time()
    valid_entries = sum(1 for entry in _cache.values() if now < entry['expires_at'])
    return {
        'total_entries': len(_cache),
        'valid_entries': valid_entries,
        'expired_entries': len(_cache) - valid_entries
    }