"""Suite de verificación de remediaciones de seguridad y arquitectura (13 problemas)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from agentic_os.execution.executor import Executor
from agentic_os.execution.tools import build_default_registry
from agentic_os.infrastructure.config.settings import settings
from agentic_os.infrastructure.persistence.jsonl import JsonlEventLog
from agentic_os.infrastructure.tenancy.models import Tenant, TenantConfig, validate_slug
from agentic_os.infrastructure.tenancy.registry import TenantRegistry
from agentic_os.kernel.policy.engine import PolicyEngine
from agentic_os.kernel.policy.models import Policy, PolicyRule
from agentic_os.kernel.world.events import Event


@pytest.fixture()
def client_env(monkeypatch, tmp_path):
    from agentic_os.interfaces.api import rest as rest_mod

    log = JsonlEventLog(base_dir=tmp_path / "eventlog")
    monkeypatch.setattr(rest_mod, "_event_log", log)
    monkeypatch.setattr(rest_mod, "TENANTS_DATA_DIR", tmp_path / "tenants")
    monkeypatch.setattr(rest_mod, "CONVERSATIONS_DIR", tmp_path / "conversations_legacy")
    monkeypatch.setattr(settings, "admin_api_key", "secret-admin-master-key")
    monkeypatch.setattr(settings, "dev_allow_all", False)

    (tmp_path / "tenants").mkdir(parents=True, exist_ok=True)
    (tmp_path / "conversations_legacy").mkdir(parents=True, exist_ok=True)

    # Crear tenant A con key y tenant B sin key (para probar el rechazo)
    reg = rest_mod._tenant_registry
    ta = Tenant(
        slug="tenant-a",
        config=TenantConfig(
            name="Tenant A",
            domain="generic",
            data_dir=str(tmp_path / "tenants" / "tenant-a"),
            enabled_capabilities=["gmail_send", "calendar_create_event"],
            credentials={"api_key": "key-tenant-a"},
        ),
    )
    tb_no_key = Tenant(
        slug="tenant-b-nokey",
        config=TenantConfig(
            name="Tenant B Sin Key",
            domain="generic",
            data_dir=str(tmp_path / "tenants" / "tenant-b-nokey"),
            enabled_capabilities=[],
            credentials={},  # sin API key
        ),
    )
    reg._tenants[ta.id] = ta
    reg._slug_index[ta.slug] = ta.id
    reg._tenants[tb_no_key.id] = tb_no_key
    reg._slug_index[tb_no_key.slug] = tb_no_key.id

    yield {
        "client": TestClient(rest_mod.app),
        "ta": ta,
        "tb": tb_no_key,
        "log": log,
        "rest_mod": rest_mod,
    }

    reg._tenants.pop(ta.id, None)
    reg._slug_index.pop(ta.slug, None)
    reg._tenants.pop(tb_no_key.id, None)
    reg._slug_index.pop(tb_no_key.slug, None)


# ------------------------------------------------------------- 1. /api/state aislamiento
def test_api_state_esta_aislado_por_tenant(client_env):
    c = client_env["client"]
    log = client_env["log"]
    ta = client_env["ta"]

    # Agregar eventos a Tenant A y a Tenant B
    log.append(Event(kind="EvA1", entity_id="1", tenant_id=ta.id))
    log.append(Event(kind="EvA2", entity_id="2", tenant_id=ta.id))
    log.append(Event(kind="EvB1", entity_id="3", tenant_id="tenant-b"))

    r_a = c.get("/api/state", headers={"X-Tenant-Id": ta.id, "X-Api-Key": "key-tenant-a"})
    assert r_a.status_code == 200
    assert r_a.json()["event_count"] == 2  # Solo los de Tenant A

    r_sys = c.get("/api/state")  # Scope 'system'
    assert r_sys.status_code == 200
    assert r_sys.json()["event_count"] == 0


# ------------------------------------------------------------- 2. /api/tasks aislamiento
def test_api_tasks_esta_aislado_por_tenant(client_env):
    c = client_env["client"]
    rest_mod = client_env["rest_mod"]
    ta = client_env["ta"]

    with rest_mod._tasks_lock:
        rest_mod._background_tasks["task_a"] = {
            "id": "task_a",
            "tenant_id": ta.id,
            "status": "completed",
            "message": "tarea de A",
            "summary": "ok",
        }
        rest_mod._background_tasks["task_b"] = {
            "id": "task_b",
            "tenant_id": "otro-tenant",
            "status": "running",
            "message": "tarea secreta de B",
            "summary": "",
        }

    r_a = c.get("/api/tasks", headers={"X-Tenant-Id": ta.id, "X-Api-Key": "key-tenant-a"})
    assert r_a.status_code == 200
    tasks_a = r_a.json()
    assert len(tasks_a) == 1
    assert tasks_a[0]["id"] == "task_a"
    assert "tarea secreta de B" not in r_a.text


# ------------------------------------------------------------- 3. Tenant sin API Key rechazado
def test_tenant_sin_api_key_exige_admin_auth(client_env):
    c = client_env["client"]
    tb = client_env["tb"]

    # Acceso sin key a un tenant sin key -> 401
    r = c.get("/api/state", headers={"X-Tenant-Id": tb.id})
    assert r.status_code == 401

    # Acceso con admin key -> 200
    r_admin = c.get("/api/state", headers={"X-Tenant-Id": tb.id, "X-Admin-Key": "secret-admin-master-key"})
    assert r_admin.status_code == 200


# ------------------------------------------------------------- 4. Protección /api/tenants CRUD
def test_api_tenants_mutations_requieren_admin_key(client_env):
    c = client_env["client"]
    ta = client_env["ta"]

    # POST sin admin key -> 401
    r_create_noauth = c.post("/api/tenants", json={"name": "Test", "slug": "test-unauth"})
    assert r_create_noauth.status_code == 401

    # POST con admin key -> 201
    r_create = c.post(
        "/api/tenants",
        json={"name": "Test", "slug": "test-created"},
        headers={"X-Admin-Key": "secret-admin-master-key"},
    )
    assert r_create.status_code == 201
    new_t = r_create.json()
    assert new_t["slug"] == "test-created"

    # PATCH sin admin key -> 401
    r_patch_noauth = c.patch(f"/api/tenants/{ta.id}", json={"name": "Nuevo Nombre"})
    assert r_patch_noauth.status_code == 401

    # PATCH con admin key -> 200
    r_patch = c.patch(
        f"/api/tenants/{ta.id}",
        json={"name": "Tenant A Actualizado"},
        headers={"X-Admin-Key": "secret-admin-master-key"},
    )
    assert r_patch.status_code == 200
    assert r_patch.json()["name"] == "Tenant A Actualizado"

    # DELETE sin admin key -> 401
    r_del_noauth = c.delete(f"/api/tenants/{new_t['id']}")
    assert r_del_noauth.status_code == 401

    # DELETE con admin key -> 200
    r_del = c.delete(f"/api/tenants/{new_t['id']}", headers={"X-Admin-Key": "secret-admin-master-key"})
    assert r_del.status_code == 200


# ------------------------------------------------------------- 5. Validación de slug & Anti-Path-Traversal
def test_validaciones_de_slug_rechazan_path_traversal():
    # Válidos
    assert validate_slug("acme") == "acme"
    assert validate_slug("tenant-123") == "tenant-123"
    assert validate_slug("clinica_las_palmas") == "clinica_las_palmas"

    # Inválidos (Path traversal, barras, caracteres peligrosos)
    invalid_slugs = ["../../etc", "a/b", "a\\b", "slug con espacios", "UPPERCASE_NOT_ALLOWED!", "../", ""]
    for bad in invalid_slugs:
        with pytest.raises(ValueError):
            validate_slug(bad)


# ------------------------------------------------------------- 6. Invariante del Executor (No Policy Bypass)
def test_executor_sin_policy_defaults_to_deny():
    ex = Executor(registry=build_default_registry(), policy_engine=None)
    # Por defecto debe tener un PolicyEngine seguro
    assert ex.policy is not None

    # Si la policy deniega por defecto, la ejecución debe denegarse (no bypass)
    res = ex.execute("gmail_send", {"to": "a@b.com", "subject": "s", "body": "b"}, tenant_id="t-unknown")
    assert res["success"] is False
    assert "denied" in res["error"].lower() or "habilitada" in res["error"].lower() or "policy" in res["error"].lower()


# ------------------------------------------------------------- 7. /api/execute resolución determinista
def test_api_execute_respeta_policy_del_tenant(client_env):
    c = client_env["client"]
    ta = client_env["ta"]

    # Acción no habilitada para Tenant A ("slack_send")
    r_denied = c.post(
        "/api/execute",
        json={"action": "slack_send", "params": {"channel": "general", "text": "hola"}},
        headers={"X-Tenant-Id": ta.id, "X-Api-Key": "key-tenant-a"},
    )
    assert r_denied.status_code == 200
    assert r_denied.json()["success"] is False
    assert "denegada" in r_denied.json()["error"].lower() or "denied" in r_denied.json()["error"].lower() or "habilitada" in r_denied.json()["error"].lower()
