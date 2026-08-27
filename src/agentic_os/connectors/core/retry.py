from __future__ import annotations

import asyncio
from typing import Callable, Optional

from ..core.config import RetryPolicy
from ..core.errors import (
    RateLimitError,
    TimeoutError_,
    NetworkError,
    ProviderError,
)


class RetryEngine:
    """Retry engine con exponential backoff + jitter."""

    def __init__(self, policy: Optional[RetryPolicy] = None):
        self.policy = policy or RetryPolicy()

    async def run(self, fn: Callable, *args, **kwargs):
        attempt = 0
        base = self.policy.base_delay_s
        while True:
            attempt += 1
            try:
                return await fn(*args, **kwargs)
            except (RateLimitError, ProviderError, NetworkError, TimeoutError_) as e:
                retryable = getattr(e, "retryable", False)
                if (
                    attempt >= self.policy.max_attempts
                    or not retryable
                    or not self._should_retry(e)
                ):
                    raise
                delay = min(
                    base * (self.policy.backoff_multiplier ** (attempt - 1)),
                    self.policy.max_delay_s,
                )
                if self.policy.jitter:
                    import random

                    delay = delay * (0.5 + random.random())
                await asyncio.sleep(delay)

    def _should_retry(self, exc) -> bool:
        try:
            import httpx
        except Exception:
            httpx = None
        if isinstance(exc, RateLimitError):
            return True
        code = getattr(exc, "code", None)
        if code is None:
            return False
        return code in self.policy.retry_on or code >= 500
