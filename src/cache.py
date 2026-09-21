"""AETHER v8.2 — Simple in-memory cache"""
import time
from functools import wraps

_cache = {}

def cached(ttl=60):
    """decorator: cache result for ttl seconds"""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            key = (fn.__name__, args, tuple(sorted(kwargs.items())))
            now = time.time()
            if key in _cache:
                val, exp = _cache[key]
                if now < exp:
                    return val
            val = fn(*args, **kwargs)
            _cache[key] = (val, now + ttl)
            return val
        return wrapper
    return decorator

def clear():
    _cache.clear()

def stats():
    return {"entries": len(_cache)}
