"""FASE 1.4 - Unificación temporal: TokenManager usa now_utc() canónico.

Verifica que `TokenManager.is_expired` compara contra `now_utc()` (reloj
canónico del kernel), normalizando timestamps naive a UTC en lugar de usar
`datetime.now()` local (reloj no inyectable).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from agentic_os.connectors.auth.token_manager import TokenManager
from agentic_os.kernel.types.time import now_utc


def test_none_expires_at_not_expired() -> None:
    assert TokenManager.is_expired(None) is False


def test_naive_timestamp_interpreted_as_utc_future_not_expired() -> None:
    future_naive = (now_utc() + timedelta(hours=1)).replace(tzinfo=None)
    assert TokenManager.is_expired(future_naive) is False


def test_naive_timestamp_interpreted_as_utc_past_is_expired() -> None:
    past_naive = (now_utc() - timedelta(hours=1)).replace(tzinfo=None)
    assert TokenManager.is_expired(past_naive) is True


def test_aware_utc_future_not_expired() -> None:
    assert TokenManager.is_expired(now_utc() + timedelta(minutes=5)) is False


def test_aware_utc_past_is_expired() -> None:
    assert TokenManager.is_expired(now_utc() - timedelta(minutes=5)) is True


def test_aware_other_tz_normalized_to_utc() -> None:
    # +02:00 futuro -> sigue sin expirar; comprueba normalización de zona.
    other_tz = timezone(timedelta(hours=2))
    future_local = now_utc().astimezone(other_tz) + timedelta(hours=2)
    assert TokenManager.is_expired(future_local) is False


def test_source_uses_now_utc_not_datetime_now_local() -> None:
    import inspect

    from agentic_os.connectors.auth import token_manager as tm

    source = inspect.getsource(tm.TokenManager.is_expired)
    assert "now_utc()" in source, "is_expired debe comparar contra now_utc()"
    assert "datetime.now(" not in source, "no debe usar reloj local no canónico"