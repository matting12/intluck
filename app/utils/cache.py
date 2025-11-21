__all__ = [
    'get_cached',
    'set_cached',
    'clear_cache',
    'get_cache_stats',
    'ONE_HOUR',
    'ONE_DAY',
    'SEVEN_DAYS'
]

import time
import hashlib
import json
from typing import Any

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
    """Get value from cache if exists and not expired"""
    key = _make_key(prefix, params)
    
    if key in _cache:
        entry = _cache[key]
        if time.time() < entry['expires_at']:
            return entry['value']
        else:
            del _cache[key]
    
    return None


def set_cached(prefix: str, params: dict, value: Any, ttl: int = ONE_DAY) -> None:
    """Store value in cache with TTL"""
    key = _make_key(prefix, params)
    _cache[key] = {
        'value': value,
        'expires_at': time.time() + ttl
    }


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