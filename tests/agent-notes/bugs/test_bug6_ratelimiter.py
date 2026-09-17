"""Bug 6 - RateLimiter roto: check() usa ventana de 1s pero compara con requests_per_minute"""

import time
import pytest
from agentic_os.connectors.core.rate_limiter import RateLimiter
from agentic_os.connectors.core.config import RateLimitPolicy


def test_rate_limiter_per_minute_blocks_after_limit():
    """RateLimiter con requests_per_minute=5 debe bloquear el sexto request."""
    limiter = RateLimiter()
    policy = RateLimitPolicy(requests_per_minute=5, requests_per_second=None)
    limiter.register("test-key", policy)

    # Los primeros 5 deben pasar
    for i in range(5):
        assert limiter.check("test-key"), f"Request {i+1} debería permitirse"

    # El 6º debe bloquearse
    assert not limiter.check("test-key"), "Request 6 debería bloquearse (rate limit)"


def test_rate_limiter_per_second_blocks_after_limit():
    """RateLimiter con requests_per_second=2 debe bloquear el tercer request en 1 segundo."""
    limiter = RateLimiter()
    policy = RateLimitPolicy(requests_per_minute=None, requests_per_second=2)
    limiter.register("test-rps", policy)

    assert limiter.check("test-rps"), "Primer request debería permitirse"
    assert limiter.check("test-rps"), "Segundo request debería permitirse"
    assert not limiter.check("test-rps"), "Tercer request debería bloquearse (rate limit por segundo)"


def test_rate_limiter_resets_after_window():
    """Después de la ventana de tiempo, el rate limiter debe resetear."""
    limiter = RateLimiter()
    policy = RateLimitPolicy(requests_per_minute=2, requests_per_second=None)
    limiter.register("test-reset", policy)

    # Agotar el límite
    assert limiter.check("test-reset")
    assert limiter.check("test-reset")
    assert not limiter.check("test-reset"), "Debe bloquear después del límite"

    # Manipular el tiempo para simular que pasó la ventana (60s)
    # Restamos 61 segundos del contador
    from collections import deque
    limiter._counters["test-reset"] = deque(
        [t - 61.0 for t in limiter._counters["test-reset"]]
    )
    assert limiter.check("test-reset"), "Debe resetear después de la ventana"


def test_rate_limiter_unregistered_key_allows_all():
    """Un key no registrado debe permitir todo (fail-open para no bloquear sin config)."""
    limiter = RateLimiter()
    for _ in range(100):
        assert limiter.check("unregistered-key")


def test_rate_limiter_dont_count_blocked_requests():
    """Las requests bloqueadas no deben contarse hacia el límite."""
    limiter = RateLimiter()
    policy = RateLimitPolicy(requests_per_minute=3, requests_per_second=None)
    limiter.register("test-count", policy)

    assert limiter.check("test-count")  # 1
    assert limiter.check("test-count")  # 2
    assert limiter.check("test-count")  # 3
    assert not limiter.check("test-count")  # bloqueada, no cuenta
    assert not limiter.check("test-count")  # sigue bloqueada
