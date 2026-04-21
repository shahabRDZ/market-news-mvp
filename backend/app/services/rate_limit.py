from __future__ import annotations

import threading
import time
from collections import defaultdict
from dataclasses import dataclass


@dataclass
class _Counter:
    window_start: float
    count: int


class RateLimiter:
    """Simple per-key fixed-window limiter. In-process; swap for Redis in prod."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters: dict[str, _Counter] = defaultdict(lambda: _Counter(time.time(), 0))

    def check(self, key: str, limit: int, window_seconds: int) -> tuple[bool, int, int]:
        if limit <= 0:
            return False, 0, window_seconds
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


rate_limiter = RateLimiter()
