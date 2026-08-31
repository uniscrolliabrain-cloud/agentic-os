"""Hardening FASE 1: credenciales nunca por la API + DEV_ALLOW_ALL explícito.

1.1 Un tenant con credentials en su config NUNCA filtra "secret" por la API.
1.2 Con DEV_ALLOW_ALL=false, un tenant sin enabled_capabilities recibe deny
    para cualquier capability, en cualquier ENV.
"""

import os

import pytest
from fastapi.testclient import TestClient

from agentic_os.infrastructure.config.settings import settings
from agentic_os.infrastructure.tenancy.models import TenantConfig, TenantConfigPublic
from agentic_os.kernel.policy.engine import PolicyEngine, default_policy


def _tenant_config(credentials: dict, enabled_capabilities: list | None = None) -> TenantConfig:
    return TenantConfig(
        name="Acme",
        domain="generic",
        data_dir="data/tenants/acme",
        enabled_capabilities=enabled_capabilities or [],
        credentials=credentials,
    )


# ---------------------------------------------------------------- 1.1 ---------
def test_tenant_public_nunca_expone_credentials():
    cfg = _tenant_config(credentials={"hubspot": {"token": "secret-abc"}})
    pub = TenantConfigPublic.from_config(cfg)
    assert "credentials" not in pub.model_fields
    assert "token" not in pub.model_dump_json()
    assert "secret-abc" not in pub.model_dump_json()
    assert "hubspot" in pub.connected_providers  # solo el nombre, no el valor


def test_api_tenants_nunca_filtra_secret(monkeypatch):
    """GET /api/tenants con un tenant cuya config tiene credentials NUNCA
    devuelve el valor en el body."""
    from agentic_os.infrastructure.tenancy.registry import TenantRegistry
    from agentic_os.infrastructure.tenancy.models import Tenant
    from agentic_os.interfaces.api import rest as rest_mod

    # preparar un tenant con credencial sensible en el registry compartido
    t = Tenant(slug="acme", config=_tenant_config(credentials={"hubspot": {"token": "secret-xyz"}}))
    registry = TenantRegistry()
    reg = registry or rest_mod._tenant_registry
    # registro limpio
    for old in list(reg._tenants.values()):
        pass
    # inyectar en memoria
    rest_mod._tenant_registry._tenants[t.id] = t
    rest_mod._tenant_registry._slug_index[t.slug] = t.id
    try:
        with TestClient(rest_mod.app) as client:
            r = client.get("/api/tenants")
            assert r.status_code == 200
            assert "secret-xyz" not in r.text
            assert "credentials" not in r.text
            # conectado visible solo como nombre
            assert "hubspot" in r.text
    finally:
        rest_mod._tenant_registry._tenants.pop(t.id, None)
        rest_mod._tenant_registry._slug_index.pop(t.slug, None)


# ---------------------------------------------------------------- 1.2 ---------
def test_dev_allow_all_false_deny_sin_capabilities(monkeypatch):
    """Con DEV_ALLOW_ALL=false (default), un tenant sin enabled_capabilities recibe deny."""
    from agentic_os.infrastructure.tenancy.registry import TenantRegistry
    from agentic_os.infrastructure.tenancy.models import Tenant

    monkeypatch.delenv("DEV_ALLOW_ALL", raising=False)
    t_deny = Tenant(slug="sin-caps", config=_tenant_config(credentials={}, enabled_capabilities=[]))
    d = PolicyEngine().can_for_tenant(t_deny.id, "crm.contact.create")
    assert d.effect == "deny", d
    assert d.reason


def test_dev_allow_all_true_permite_si_capability_habilitada(monkeypatch):
    """Con DEV_ALLOW_ALL=true y tenant con enabled_capabilities que incluye la
    capability, la decisión sí es allow. (El allow-all nunca salta el aislamiento.)"""
    from agentic_os.infrastructure.tenancy.registry import TenantRegistry
    from agentic_os.infrastructure.tenancy.models import Tenant

    monkeypatch.setenv("DEV_ALLOW_ALL", "true")
    reg = TenantRegistry()
    t = Tenant(
        slug="con-cap",
        config=_tenant_config(credentials={}, enabled_capabilities=["crm.contact.create"]),
    )
    reg.register(t)
    d = PolicyEngine().can_for_tenant(t.id, "crm.contact.create")
    assert d.effect == "allow", d
    # aunque DEV_ALLOW_ALL=true, una capability NO habilitada para el tenant -> deny
    d2 = PolicyEngine().can_for_tenant(t.id, "gmail_send")
    assert d2.effect == "deny", d2


def test_default_policy_sin_dev_allow_all_es_deny(monkeypatch):
    """default_policy() sin DEV_ALLOW_ALL genera deny-all (incluso en dev)."""
    monkeypatch.delenv("DEV_ALLOW_ALL", raising=False)
    p = default_policy("t")
    assert p.rules == []  # sin reglas = deny by default
    assert not any(r.effect == "allow" for r in p.rules)