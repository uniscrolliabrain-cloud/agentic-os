"""Bloque 0b: feature flags + stubs (BUILD_PLAN)."""
from __future__ import annotations

import pytest

from agentic_os.infrastructure.auth.stub import AuthStub, LocalUser, get_auth
from agentic_os.infrastructure.config.feature_flags import (
    FeatureFlags,
    load_feature_flags,
)
from agentic_os.orchestration.temporal.stub import (
    StubWorkflowHandle,
    TemporalStub,
    get_temporal_client,
)


# ---------------------------------------------- feature_flags

def test_default_flags_todo_off_excepto_web_search():
    f = FeatureFlags()
    assert f.temporal is False
    assert f.supabase is False
    assert f.jwt is False
    assert f.obs is False
    assert f.redis is False
    assert f.docker is False
    assert f.gmail is False
    assert f.drive is False
    assert f.calendar is False
    assert f.discord is False
    assert f.web_search is True


def test_is_enabled_fail_closed_si_no_existe():
    f = FeatureFlags()
    assert f.is_enabled("temporal") is False
    assert f.is_enabled("inventado") is False
    assert f.is_enabled("web_search") is True


def test_is_enabled_normaliza_nombre():
    f = FeatureFlags(temporal=True)
    assert f.is_enabled("TEMPORAL") is True
    assert f.is_enabled(" temporal ") is True


def test_load_feature_flags_lee_env(monkeypatch):
    monkeypatch.setenv("ENABLE_TEMPORAL", "true")
    monkeypatch.setenv("ENABLE_DISCORD", "1")
    monkeypatch.setenv("ENABLE_SUPABASE", "false")
    f = load_feature_flags()
    assert f.temporal is True
    assert f.discord is True
    assert f.supabase is False


def test_load_feature_flags_default_si_env_missing(monkeypatch):
    for k in ("ENABLE_TEMPORAL", "ENABLE_DISCORD", "ENABLE_WEB_SEARCH"):
        monkeypatch.delenv(k, raising=False)
    f = load_feature_flags()
    assert f.temporal is False
    assert f.discord is False
    assert f.web_search is True


def test_as_dict():
    d = FeatureFlags().as_dict()
    assert "temporal" in d
    assert "web_search" in d
    assert all(isinstance(v, bool) for v in d.values())


# ---------------------------------------------- temporal stub

@pytest.mark.asyncio
async def test_temporal_stub_devuelve_handle():
    s = TemporalStub()
    h = await s.start_workflow("wf", args=[1])
    assert isinstance(h, StubWorkflowHandle)
    assert h.id.startswith("stub-wf-")


@pytest.mark.asyncio
async def test_temporal_stub_ejecuta_activity_inline():
    s = TemporalStub()

    async def double(x):
        return x * 2

    result = await s.execute_activity(double, 21)
    assert result == 42


@pytest.mark.asyncio
async def test_get_temporal_client_devuelve_stub_por_defecto(monkeypatch):
    monkeypatch.delenv("ENABLE_TEMPORAL", raising=False)
    c = await get_temporal_client()
    assert isinstance(c, TemporalStub)


# ---------------------------------------------- auth stub

def test_auth_stub_usuario_local():
    a = AuthStub()
    u = a.current_user()
    assert isinstance(u, LocalUser)
    assert u.user_id == "local-user"
    assert u.role == "director"


def test_get_auth_devuelve_singleton():
    a1 = get_auth()
    a2 = get_auth()
    assert a1 is a2


def test_local_user_es_frozen():
    from pydantic import ValidationError
    u = LocalUser()
    with pytest.raises(ValidationError):
        u.user_id = "otro"

