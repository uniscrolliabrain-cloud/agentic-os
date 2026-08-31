"""Hardening FASE 4: tenant scoping real (lecturas aisladas por cabecera).

Criterio de aceptación: una petición con X-Tenant-Id: A nunca puede leer
eventos ni conversaciones de tenant B, aunque conozca el conversation_id.
Además: tenant desconocido -> 404; tenant con api_key exige X-Api-Key -> 401.
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from agentic_os.infrastructure.persistence.jsonl import JsonlEventLog
from agentic_os.infrastructure.tenancy.models import Tenant, TenantConfig
from agentic_os.kernel.world.events import Event


def _make_tenant(slug: str, credentials: dict | None = None) -> Tenant:
    return Tenant(
        slug=slug,
        config=TenantConfig(
            name=slug.upper(),
            domain="generic",
            data_dir=f"data/tenants/{slug}",
            enabled_capabilities=[],
            credentials=credentials or {},
        ),
    )


@pytest.fixture()
def client(monkeypatch, tmp_path):
    """TestClient con eventlog y carpetas de datos aisladas en tmp_path."""
    from agentic_os.interfaces.api import rest as rest_mod

    # eventlog temporal (no escribir en data/ del repo)
    log = JsonlEventLog(base_dir=tmp_path / "eventlog")
    monkeypatch.setattr(rest_mod, "_event_log", log)
    # carpetas de conversaciones temporales
    monkeypatch.setattr(rest_mod, "TENANTS_DATA_DIR", tmp_path / "tenants")
    monkeypatch.setattr(rest_mod, "CONVERSATIONS_DIR", tmp_path / "conversations_legacy")
    (tmp_path / "tenants").mkdir(parents=True)
    (tmp_path / "conversations_legacy").mkdir(parents=True)

    # tenants A y B en memoria (limpiamos al terminar)
    ta, tb = _make_tenant("tenant-a"), _make_tenant("tenant-b")
    tc = _make_tenant("tenant-sec", credentials={"api_key": "k-secure-123"})
    reg = rest_mod._tenant_registry
    for t in (ta, tb, tc):
        reg._tenants[t.id] = t
        reg._slug_index[t.slug] = t.id
    yield {"client": TestClient(rest_mod.app), "a": ta, "b": tb, "c": tc, "log": log}
    for t in (ta, tb, tc):
        reg._tenants.pop(t.id, None)
        reg._slug_index.pop(t.slug, None)


def _header(tenant_id: str, api_key: str | None = None) -> dict:
    h = {"X-Tenant-Id": tenant_id}
    if api_key:
        h["X-Api-Key"] = api_key
    return h


# ------------------------------------------------- aislamiento de lecturas ---
def test_tenant_a_nunca_lee_eventos_de_tenant_b(client):
    c = client["client"]
    ev = Event(
        kind="SecretoInterno",
        entity_id="ent-b",
        payload={"nota": "dato-de-B"},
        actor_id="tester",
        tenant_id=client["b"].id,
    )
    client["log"].append(ev)

    r = c.get("/api/events", headers=_header(client["a"].id))
    assert r.status_code == 200
    body = r.text
    assert "dato-de-B" not in body
    assert "SecretoInterno" not in body
    # el propio tenant A sí ve lo suyo
    ev_a = Event(kind="DeA", entity_id="ent-a", payload={"x": "1"}, actor_id="t", tenant_id=client["a"].id)
    client["log"].append(ev_a)
    r2 = c.get("/api/events", headers=_header(client["a"].id))
    assert "DeA" in r2.text


def test_tenant_a_nunca_lee_conversacion_de_tenant_b(client):
    c = client["client"]
    # B crea su conversación
    r = c.post("/api/conversations", headers=_header(client["b"].id))
    assert r.status_code == 201
    conv_b = r.json()

    # A conoce el conversation_id de B y aun así no puede leerla
    r_get = c.get(f"/api/conversations/{conv_b['id']}", headers=_header(client["a"].id))
    assert r_get.status_code == 404
    # ni borrarla
    r_del = c.delete(f"/api/conversations/{conv_b['id']}", headers=_header(client["a"].id))
    assert r_del.status_code == 404
    # ni verla en el listado
    r_list = c.get("/api/conversations", headers=_header(client["a"].id))
    assert r_list.status_code == 200
    assert all(item["id"] != conv_b["id"] for item in r_list.json())
    # el dueño sí la ve
    r_owner = c.get(f"/api/conversations/{conv_b['id']}", headers=_header(client["b"].id))
    assert r_owner.status_code == 200
    assert r_owner.json()["tenant_id"] == client["b"].id


def test_conversacion_creada_lleva_tenant_id_y_ruta_por_tenant(client, tmp_path):
    c = client["client"]
    r = c.post("/api/conversations", headers=_header(client["a"].id))
    assert r.status_code == 201
    conv = r.json()
    assert conv["tenant_id"] == client["a"].id
    path = tmp_path / "tenants" / client["a"].id / "conversations" / f"{conv['id']}.json"
    assert path.exists()


# ------------------------------------------------------- acceso por header ---
def test_tenant_desconocido_da_404(client):
    c = client["client"]
    r = c.get("/api/events", headers=_header("no-existe-xyz"))
    assert r.status_code == 404


def test_tenant_con_api_key_la_exige(client):
    c = client["client"]
    tid = client["c"].id
    # sin X-Api-Key -> 401
    assert c.get("/api/events", headers=_header(tid)).status_code == 401
    # X-Api-Key incorrecta -> 401
    assert c.get("/api/events", headers=_header(tid, "mala-key")).status_code == 401
    # correcta -> 200
    assert c.get("/api/events", headers=_header(tid, "k-secure-123")).status_code == 200


def test_anonimo_solo_ve_scope_system(client):
    c = client["client"]
    ev = Event(kind="DeB", entity_id="e", payload={}, actor_id="t", tenant_id=client["b"].id)
    client["log"].append(ev)
    r = c.get("/api/events")  # sin cabecera
    assert r.status_code == 200
    assert "DeB" not in r.text