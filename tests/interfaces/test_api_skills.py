"""API: instalación de Prompt Skills vía POST /api/skills/install.

Cubre los puntos del feedback PR #1: tests multi-tenant (aislamiento por
cabecera X-Tenant-Id, rechazo sin tenant válido, no-injerencia entre tenants).
"""

import pytest
from fastapi.testclient import TestClient

import agentic_os.cognition.skills.library as lib
from agentic_os.infrastructure.persistence.memory import InMemoryEventLog
from agentic_os.infrastructure.tenancy.models import Tenant, TenantConfig

VALID_MD = """---
name: inbox_cero
description: Procesar email y proponer Intent
version: 1.0.0
pipeline_id: inbox_zero
---
Sigue el skill inbox_zero. Lee el inbox, clasifica y propón un intent.
"""

VALID_MD_MEET = VALID_MD.replace(
    "name: inbox_cero\n", "name: meeting_plan\n"
).replace(
    "pipeline_id: inbox_zero", "pipeline_id: schedule_meeting"
)


@pytest.fixture()
def client_env(monkeypatch, tmp_path):
    from agentic_os.interfaces.api import rest as rest_mod
    from agentic_os.infrastructure.config.settings import settings
    from agentic_os.infrastructure.tenancy.registry import TenantRegistry

    # Aislamiento del almacén global, del eventlog y del tenant registry:
    # NUNCA mutamos el registry global de rest.py (evita contaminar otros tests).
    fresh_store = lib.MemoryStore()
    fresh_log = InMemoryEventLog()
    monkeypatch.setattr(lib, "PROMPT_SKILLS", fresh_store)
    monkeypatch.setattr(lib, "get_eventlog_repo", lambda: fresh_log)
    monkeypatch.setattr(settings, "admin_api_key", "admin-key")

    fresh_reg = TenantRegistry()
    ta = Tenant(
        slug="tenant-a",
        config=TenantConfig(
            name="Tenant A",
            domain="generic",
            data_dir=str(tmp_path / "t-a"),
            enabled_capabilities=["gmail_read", "gmail_send"],
            credentials={"api_key": "key-tenant-a"},
        ),
    )
    tb = Tenant(
        slug="tenant-b",
        config=TenantConfig(
            name="Tenant B",
            domain="generic",
            data_dir=str(tmp_path / "t-b"),
            enabled_capabilities=["calendar_create_event"],
            credentials={"api_key": "key-tenant-b"},
        ),
    )
    fresh_reg._tenants[ta.id] = ta
    fresh_reg._slug_index[ta.slug] = ta.id
    fresh_reg._tenants[tb.id] = tb
    fresh_reg._slug_index[tb.slug] = tb.id
    monkeypatch.setattr(rest_mod, "_tenant_registry", fresh_reg)

    client = TestClient(rest_mod.app)
    return client, ta, tb, fresh_store, fresh_log


def _install(client, tenant_id, api_key, content=VALID_MD):
    return client.post(
        "/api/skills/install",
        json={"content": content},
        headers={"X-Tenant-Id": tenant_id, "X-Api-Key": api_key},
    )


def test_install_skill_endpoint_ok(client_env):
    client, tenant, _tb, store, log = client_env
    resp = _install(client, tenant.id, "key-tenant-a")
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["id"] == "skill:inbox_cero:prompt"
    assert body["pipeline_id"] == "inbox_zero"
    assert body["content_md5"]
    # Persistido en el almacén de prompt skills del sistema.
    assert store.get(body["id"]) is not None
    # Evento SkillInstalled auditado.
    assert any(e.kind == "SkillInstalled" for e in log.list_all())


def test_install_skill_endpoint_fail_closed(client_env):
    client, tenant, _tb, store, _log = client_env
    bad_md = VALID_MD.replace("pipeline_id: inbox_zero", "pipeline_id: no_existe")
    resp = _install(client, tenant.id, "key-tenant-a", content=bad_md)
    assert resp.status_code == 400
    assert "no existe un Skill ejecutable" in resp.json()["detail"]
    assert len(store) == 0


# ------------------------------------------------ multi-tenant (PR #1) ----
def test_install_sin_api_key_o_con_key_invalida_rechazado(client_env):
    client, tenant, _tb, store, _log = client_env
    # Sin API key (tenant con credencial requerida) → 401.
    resp = client.post(
        "/api/skills/install",
        json={"content": VALID_MD},
        headers={"X-Tenant-Id": tenant.id},
    )
    assert resp.status_code == 401
    assert len(store) == 0

    # API key incorrecta → 401.
    resp = _install(client, tenant.id, "clave-incorrecta")
    assert resp.status_code == 401
    assert len(store) == 0


def test_install_tenant_inexistente_rechazado(client_env):
    client, _ta, _tb, store, _log = client_env
    resp = _install(client, "tenant-que-no-existe", "key-tenant-a")
    assert resp.status_code == 404
    assert len(store) == 0


def test_aislamiento_por_tenant_en_instalacion(client_env):
    client, ta, tb, store, _log = client_env
    from agentic_os.cognition.memory.retrieval import retrieve_prompt_skills

    _install(client, ta.id, "key-tenant-a", content=VALID_MD)
    _install(client, tb.id, "key-tenant-b", content=VALID_MD_MEET)

    # Cada ficha quedó registrada SOLO para su tenant.
    a_item = store.get("skill:inbox_cero:prompt")
    b_item = store.get("skill:meeting_plan:prompt")
    assert a_item.metadata["tenant_id"] == ta.id
    assert b_item.metadata["tenant_id"] == tb.id

    # Un tenant NO puede recuperar los skills instalados por el otro.
    hits_a = retrieve_prompt_skills(store, "inbox", tenant_id=ta.id)
    hits_b = retrieve_prompt_skills(store, "inbox", tenant_id=tb.id)
    assert all(item.metadata["tenant_id"] == ta.id for item, _ in hits_a)
    # El skill de B no aparece para A (y A no aparece para B).
    assert not any(item.metadata["tenant_id"] == tb.id for item, _ in hits_a)
    assert not any(item.metadata["tenant_id"] == ta.id for item, _ in hits_b)


# ----------------------------------------- ejecución multi-tenant (PR #1) --
class _RecordingTool:
    """Tool sin efectos externos que registra las llamadas."""

    def __init__(self, name: str):
        self.name = name
        self.calls = []

    def run(self, params: dict) -> dict:
        self.calls.append(dict(params))
        return {"status": "ok", "tool": self.name}


@pytest.fixture()
def run_env(monkeypatch, tmp_path):
    """Fixture para /api/skills/run con Executor mockeado (sin conectores)."""
    from agentic_os.execution.executor import Executor
    from agentic_os.execution.tools import ToolRegistry
    from agentic_os.interfaces.api import rest as rest_mod
    from agentic_os.infrastructure.config.settings import settings
    from agentic_os.infrastructure.tenancy.registry import TenantRegistry

    monkeypatch.setenv("DEV_ALLOW_ALL", "true")  # aisla policy para el test
    store = lib.MemoryStore()
    log = InMemoryEventLog()
    monkeypatch.setattr(lib, "PROMPT_SKILLS", store)
    monkeypatch.setattr(lib, "get_eventlog_repo", lambda: log)
    monkeypatch.setattr(settings, "admin_api_key", "admin-key")

    registry = ToolRegistry()
    gmail = _RecordingTool("gmail_send")
    doc = _RecordingTool("documentation_create")
    registry.register(gmail)
    registry.register(doc)
    monkeypatch.setattr(
        rest_mod, "_executor", Executor(registry=registry, event_log=log)
    )

    fresh_reg = TenantRegistry()
    ta = Tenant(
        slug="tenant-a",
        config=TenantConfig(
            name="Tenant A",
            domain="generic",
            data_dir=str(tmp_path / "t-a"),
            enabled_capabilities=["gmail_send", "documentation_create"],
            credentials={"api_key": "key-tenant-a"},
        ),
    )
    tb = Tenant(
        slug="tenant-b",
        config=TenantConfig(
            name="Tenant B",
            domain="generic",
            data_dir=str(tmp_path / "t-b"),
            enabled_capabilities=["calendar_create_event"],
            credentials={"api_key": "key-tenant-b"},
        ),
    )
    fresh_reg._tenants[ta.id] = ta
    fresh_reg._slug_index[ta.slug] = ta.id
    fresh_reg._tenants[tb.id] = tb
    fresh_reg._slug_index[tb.slug] = tb.id
    monkeypatch.setattr(rest_mod, "_tenant_registry", fresh_reg)

    client = TestClient(rest_mod.app)
    return client, ta, tb, gmail, doc, log


def _run_skill(client, tenant_id, api_key, kind="send_email_sop"):
    return client.post(
        "/api/skills/run",
        json={"intent": {"goal": "enviar email", "kind": kind, "payload": "{}"}},
        headers={"X-Tenant-Id": tenant_id, "X-Api-Key": api_key},
    )


def test_run_skill_ok_para_tenant_con_capability_habilitada(run_env):
    client, ta, _tb, gmail, doc, _log = run_env
    resp = _run_skill(client, ta.id, "key-tenant-a")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True, body
    tools = [s["tool"] for s in body["result"]]
    assert tools == ["gmail_send", "documentation_create"]
    assert gmail.calls and doc.calls  # pasos del Skill frozen en orden


def test_run_skill_bloqueado_para_tenant_sin_capability(run_env):
    """Feedback PR #1: un tenant no puede ejecutar skills con capabilities que
    su tenant no tiene habilitadas (aislamiento real vía PolicyEngine)."""
    client, _ta, tb, gmail, doc, log = run_env
    resp = _run_skill(client, tb.id, "key-tenant-b")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is False
    assert "no habilitada" in body["error"] or "denegada" in body["error"]
    # La tool NO se ejecutó para el tenant sin la capability.
    assert gmail.calls == []
    assert doc.calls == []
    # Y el fallo quedó auditado en el eventlog del tenant B.
    assert any(
        e.kind == "SkillBlocked"
        for e in log.list_for_tenant(tb.id)
    )