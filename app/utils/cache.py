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

import sqlite3
import tempfile

# On by default; set CACHE_ENABLED=false to turn off.
_CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() != "false"

# SQLite file so all gunicorn workers on a replica share one cache (an in-memory dict
# per worker still gave different results depending on which worker answered).
# ponytail: lost on redeploy and not shared across replicas; Postgres in rebuild phase 4.
_DB_PATH = os.getenv("CACHE_DB_PATH", os.path.join(tempfile.gettempdir(), "intluck_cache.sqlite"))

# TTL constants
ONE_HOUR = 3600
ONE_DAY = 86400
SEVEN_DAYS = 604800


def _db() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH, timeout=5)
    conn.execute("CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, value TEXT, expires_at REAL)")
    return conn


def _make_key(prefix: str, params: dict) -> str:
    """Generate cache key from prefix and params"""
    param_str = json.dumps(params, sort_keys=True)
    hash_str = hashlib.md5(param_str.encode()).hexdigest()[:12]
    return f"{prefix}:{hash_str}"


def get_cached(prefix: str, params: dict) -> Any | None:
    """Get value from cache if exists and not expired. Returns None if cache disabled."""
    if not _CACHE_ENABLED:
        return None
    with _db() as conn:
        row = conn.execute("SELECT value FROM cache WHERE key = ? AND expires_at > ?",
                           (_make_key(prefix, params), time.time())).fetchone()
    return json.loads(row[0]) if row else None


def set_cached(prefix: str, params: dict, value: Any, ttl: int = ONE_DAY) -> None:
    """Store value in cache with TTL. No-op if cache disabled."""
    if not _CACHE_ENABLED:
        return
    with _db() as conn:
        conn.execute("INSERT OR REPLACE INTO cache VALUES (?, ?, ?)",
                     (_make_key(prefix, params), json.dumps(value), time.time() + ttl))


def clear_cache() -> None:
    """Clear all cached entries"""
    with _db() as conn:
        conn.execute("DELETE FROM cache")


def get_cache_stats() -> dict:
    """Return cache statistics for debugging"""
    with _db() as conn:
        total, valid = conn.execute("SELECT COUNT(*), COALESCE(SUM(expires_at > ?), 0) FROM cache",
                                    (time.time(),)).fetchone()
    return {'total_entries': total, 'valid_entries': valid, 'expired_entries': total - valid}


if __name__ == "__main__":
    _DB_PATH = os.path.join(tempfile.mkdtemp(), "selfcheck.sqlite")
    _CACHE_ENABLED = True
    set_cached("t", {"a": 1}, {"links": [1, 2]})
    assert get_cached("t", {"a": 1}) == {"links": [1, 2]}
    set_cached("t", {"a": 2}, {"x": 1}, ttl=-1)
    assert get_cached("t", {"a": 2}) is None
    assert get_cache_stats() == {'total_entries': 2, 'valid_entries': 1, 'expired_entries': 1}
    clear_cache()
    assert get_cached("t", {"a": 1}) is None
    print("cache self-check ok")
