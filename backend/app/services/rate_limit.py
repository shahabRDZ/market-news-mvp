from __future__ import annotations

import logging
import threading
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Protocol

from ..config import settings

log = logging.getLogger("rate_limit")


class _Backend(Protocol):
    def check(self, key: str, limit: int, window_seconds: int) -> tuple[bool, int, int]: ...


@dataclass
class _Counter:
    window_start: float
    count: int


class _InMemoryBackend:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters: dict[str, _Counter] = defaultdict(lambda: _Counter(time.time(), 0))

    def check(self, key: str, limit: int, window_seconds: int) -> tuple[bool, int, int]:
        now = time.time()
        with self._lock:
            c = self._counters[key]
            if now - c.window_start >= window_seconds:
                c.window_start = now
                c.count = 0
            c.count += 1
            remaining = max(0, limit - c.count)
            reset_in = int(window_seconds - (now - c.window_start))
            allowed = c.count <= limit
            return allowed, remaining, reset_in


class _RedisBackend:
    """Atomic fixed-window using INCR + EXPIRE on first hit."""

    def __init__(self, url: str) -> None:
        import redis  # local import: keeps tests/SQLite path independent of redis client

        self._r = redis.Redis.from_url(url, decode_responses=True)
        self._r.ping()

    def check(self, key: str, limit: int, window_seconds: int) -> tuple[bool, int, int]:
        rk = f"rl:{key}"
        pipe = self._r.pipeline()
        pipe.incr(rk, 1)
        pipe.ttl(rk)
        count, ttl = pipe.execute()
        if ttl is None or ttl < 0:
            self._r.expire(rk, window_seconds)
            ttl = window_seconds
        remaining = max(0, limit - int(count))
        allowed = int(count) <= limit
        return allowed, remaining, int(ttl)


class RateLimiter:
    def __init__(self) -> None:
        self._backend: _Backend
        if settings.REDIS_URL:
            try:
                self._backend = _RedisBackend(settings.REDIS_URL)
                log.info("rate limiter: redis backend at %s", settings.REDIS_URL)
            except Exception as exc:
                log.warning("redis backend unavailable (%s); falling back to in-memory", exc)
                self._backend = _InMemoryBackend()
        else:
            self._backend = _InMemoryBackend()

    def check(self, key: str, limit: int, window_seconds: int) -> tuple[bool, int, int]:
        if limit <= 0:
            return False, 0, window_seconds
        return self._backend.check(key, limit, window_seconds)


rate_limiter = RateLimiter()
