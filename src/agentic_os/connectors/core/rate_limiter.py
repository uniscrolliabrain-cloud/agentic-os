from __future__ import annotations

import time
from collections import deque
from threading import Lock

from ..core.config import RateLimitPolicy


class RateLimiter:
    """Rate limiter per-connector/per-credential.

    Supporta requests_per_minute, requests_per_second y burst_size.
    """

    def __init__(self):
        self._policies: dict[str, RateLimitPolicy] = {}
        self._counters: dict[str, deque] = {}
        self._locks: dict[str, Lock] = {}
        self._daily: dict[str, tuple[float, int]] = {}

    def register(self, key: str, policy: RateLimitPolicy) -> None:
        self._policies[key] = policy
        self._counters[key] = deque()
        self._locks.setdefault(key, Lock())
        self._daily[key] = (time.time(), 0)

    def check(self, key: str) -> bool:
        policy = self._policies.get(key)
        if not policy:
            return True
        lock = self._locks.get(key, Lock())
        with lock:
            now = time.time()
            if policy.requests_per_second:
                window = 1.0 / policy.requests_per_second
                self._trim(self._counters[key], now - window)
                if len(self._counters[key]) >= policy.requests_per_second:
                    return False
            else:
                window = 60.0
                self._trim(self._counters[key], now - 60.0)
                if len(self._counters[key]) >= policy.requests_per_minute:
                    return False
            self._counters[key].append(now)

            # daily quota
            if policy.daily_quota:
                day_start, count = self._daily.get(key, (now, 0))
                if now - day_start >= 86400:
                    self._daily[key] = (now, 1)
                elif count >= policy.daily_quota:
                    return False
                else:
                    self._daily[key] = (day_start, count + 1)
            return True

    def _trim(self, dq: deque, cutoff: float, window: float = 60.0):
        while dq and dq[0] < cutoff:
            dq.popleft()
        if len(dq) > 60:
            excess = len(dq) - 60
            for _ in range(excess):
                dq.popleft()

    def wait_time(self, key: str) -> float:
        policy = self._policies.get(key)
        if not policy or not self._counters.get(key):
            return 0.0
        if not self._counters[key]:
            return 0.0
        earliest = self._counters[key][0]
        reset_at = earliest + 60.0
        return max(0.0, reset_at - time.time())
