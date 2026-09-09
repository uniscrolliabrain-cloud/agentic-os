"""API: instalación de Prompt Skills vía POST /api/skills/install."""

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
            enabled_capabilities=["gmail_read"],
            credentials={"api_key": "key-tenant-a"},
        ),
    )
    fresh_reg._tenants[ta.id] = ta
    fresh_reg._slug_index[ta.slug] = ta.id
    monkeypatch.setattr(rest_mod, "_tenant_registry", fresh_reg)

    client = TestClient(rest_mod.app)
    return client, ta, fresh_store, fresh_log


def test_install_skill_endpoint_ok(client_env):
    client, tenant, store, log = client_env
    resp = client.post(
        "/api/skills/install",
        json={"content": VALID_MD},
        headers={"X-Tenant-Id": tenant.id, "X-Api-Key": "key-tenant-a"},
    )
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
    client, tenant, store, _log = client_env
    bad_md = VALID_MD.replace("pipeline_id: inbox_zero", "pipeline_id: no_existe")
    resp = client.post(
        "/api/skills/install",
        json={"content": bad_md},
        headers={"X-Tenant-Id": tenant.id, "X-Api-Key": "key-tenant-a"},
    )
    assert resp.status_code == 400
    assert "no existe un Skill ejecutable" in resp.json()["detail"]
    assert len(store) == 0