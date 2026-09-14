"""Tests bor-agencia (FASE 1/2, owner CLINE): tenancy scoped y entidades."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from agentic_os.domains.agencia import (
    AGENCIA_ENTITY_KINDS,
    AgencyLead,
)
from agentic_os.infrastructure.tenancy import (
    Tenant,
    TenantConfig,
    TenantConfigPublic,
    resolve_client_credentials,
)
from agentic_os.kernel.ontology.domain_models import (
    ENTITY_TYPE_REGISTRY,
    validate_registry_integrity,
)

BOR_SLUG = "bor-agencia"


def _tenant_with_clients() -> Tenant:
    return Tenant(
        slug=BOR_SLUG,
        config=TenantConfig(
            name="BOR Agency",
            domain="agencia",
            data_dir="data/tenants/bor-agencia",
            enabled_capabilities=["calendar.event.create", "whatsapp.message.send"],
            credentials={
                "api_key": "tk_test",
                "google_global": {"api_key": "g"},
                "clients": {
                    "clinica-xyz": {
                        "name": "Clinica XYZ",
                        "providers": {
                            "google": {"refresh_token": "rt-1"},
                            "hubspot": {"access_token": "hs-1"},
                        },
                    },
                    "bar-pepe": {"name": "Bar Pepe", "providers": {}},
                },
            },
        ),
    )


def test_from_config_excludes_internal_keys_but_lists_scoped() -> None:
    public = TenantConfigPublic.from_config(_tenant_with_clients().config)
    assert "clients" not in public.connected_providers
    assert "api_key" not in public.connected_providers
    assert public.connected_providers == ["google", "google_global", "hubspot"]
    assert "credentials" not in public.model_dump()


def test_from_config_no_clients_key() -> None:
    config = TenantConfig(
        name="t",
        domain="agencia",
        data_dir="d",
        credentials={"api_key": "tk_x", "stripe": {"secret_key": "s"}},
    )
    assert TenantConfigPublic.from_config(config).connected_providers == ["stripe"]


def test_resolve_returns_copy_and_none_when_missing() -> None:
    tenant = _tenant_with_clients()
    creds = resolve_client_credentials(tenant, "clinica-xyz", "google")
    assert creds == {"refresh_token": "rt-1"}
    inner = tenant.config.credentials["clients"]["clinica-xyz"]["providers"]["google"]
    assert creds is not inner
    assert resolve_client_credentials(tenant, "clinica-xyz", "stripe") is None
    assert resolve_client_credentials(tenant, "no-existe", "google") is None
    assert resolve_client_credentials(tenant, "bar-pepe", "google") is None
    assert resolve_client_credentials(tenant, "", "google") is None


def test_agencia_kinds_registered_and_integrity(agencia_registered) -> None:
    assert AGENCIA_ENTITY_KINDS == {
        "agencia.client",
        "agencia.lead",
        "agencia.appointment",
        "agencia.deal",
        "agencia.quote",
        "agencia.audit_report",
    }
    for kind in AGENCIA_ENTITY_KINDS:
        assert kind in ENTITY_TYPE_REGISTRY
    # La integridad se valida DESPUÉS de compilar la ontología con el
    # dominio y registrar sus entidades (camino canónico).
    validate_registry_integrity()


@pytest.fixture()
def agencia_registered():
    """Bootstrap explícito del dominio: compilar + registrar, y limpiar después.

    El registro del dominio NO ocurre en import (invariante del kernel): cada
    test que necesita las entidades agencia las registra aquí y restaura el
    registro core al terminar, para no contaminar otros suites.
    """
    from agentic_os.domains.agencia import AgenciaDomain

    AgenciaDomain.register_entities()
    yield
    for kind in AGENCIA_ENTITY_KINDS:
        ENTITY_TYPE_REGISTRY.pop(kind, None)


def test_agency_lead_strict_and_forbids_extra() -> None:
    AgencyLead(
        tenant_id=BOR_SLUG,
        entity_type="agencia.lead",
        client_id="clinica-xyz",
        name="Ana",
        email="ana@example.com",
        phone="+34 600 123 456",
        source="web",
    )
    with pytest.raises(ValidationError):
        AgencyLead(
            tenant_id=BOR_SLUG,
            entity_type="agencia.lead",
            client_id="clinica-xyz",
            name="Ana",
            email="sin-arroba",
            phone="+34 600 123 456",
            source="web",
        )
    with pytest.raises(ValidationError):
        AgencyLead(
            tenant_id=BOR_SLUG,
            entity_type="agencia.lead",
            client_id="clinica-xyz",
            name="Ana",
            email="ana@example.com",
            phone="+34 600 123 456",
            source="web",
            campo_inventado="x",
        )



def test_agency_client_quote_appointment_deal_audit() -> None:
    from datetime import datetime, timezone

    from agentic_os.domains.agencia import (
        AgencyAppointment,
        AgencyClient,
        AgencyDeal,
        AuditReport,
        ServiceQuote,
    )

    AgencyClient(
        tenant_id=BOR_SLUG,
        entity_type="agencia.client",
        name="Clinica",
        slug="clinica-xyz",
    )
    with pytest.raises(ValidationError):
        AgencyClient(
            tenant_id=BOR_SLUG,
            entity_type="agencia.client",
            name="Clinica",
            slug="INVALID SLUG!!",
        )
    quote = ServiceQuote(
        tenant_id=BOR_SLUG,
        entity_type="agencia.quote",
        client_id="clinica-xyz",
        service_items=[
            {"service": "web_redesign", "description": "Rediseno web", "price": 100.0},
            {"service": "seo", "description": "SEO inicial", "price": 50.5},
        ],
    )
    assert quote.total == pytest.approx(150.5)
    with pytest.raises(ValidationError):
        ServiceQuote(
            tenant_id=BOR_SLUG,
            entity_type="agencia.quote",
            client_id="clinica-xyz",
            service_items=[{"service": "seo", "description": "SEO", "price": 10.0}],
            total=999.0,
        )
    AgencyAppointment(
        tenant_id=BOR_SLUG,
        entity_type="agencia.appointment",
        client_id="clinica-xyz",
        lead_id="lead-1",
        scheduled_at=datetime(2030, 1, 1, 10, 0, tzinfo=timezone.utc),
    )
    with pytest.raises(ValidationError):
        AgencyAppointment(
            tenant_id=BOR_SLUG,
            entity_type="agencia.appointment",
            client_id="clinica-xyz",
            lead_id="lead-1",
            scheduled_at=datetime(2030, 1, 1, 10, 0),
        )
    AgencyDeal(
        tenant_id=BOR_SLUG,
        entity_type="agencia.deal",
        client_id="clinica-xyz",
        lead_id="lead-1",
        total=150.5,
    )
    report = AuditReport(
        tenant_id=BOR_SLUG,
        entity_type="agencia.audit_report",
        client_id="clinica-xyz",
        url="https://example.com",
        score=72.5,
    )
    assert report.score == pytest.approx(72.5)


POLICY_PATH = "data/policies/bor-agencia.json"


def _engine_with_tenant(monkeypatch: pytest.MonkeyPatch):
    import json

    from agentic_os.kernel.policy.engine import PolicyEngine
    from agentic_os.kernel.policy.models import Policy

    with open(POLICY_PATH, "r", encoding="utf-8") as f:
        policy = Policy(**json.load(f))
    tenant = _tenant_with_clients().model_copy(
        update={
            "config": _tenant_with_clients().config.model_copy(
                update={
                    "enabled_capabilities": [
                        "web.search",
                        "web.page.extract",
                        "web.seo.audit",
                        "web.seo.keywords",
                        "data.lead.validate",
                        "crm.contact.create",
                        "crm.contact.read",
                        "crm.deal.create",
                        "crm.task.create",
                        "calendar.event.create",
                        "calendar.event.read",
                        "whatsapp.message.send",
                        "whatsapp.template.send",
                        "payment.link.create",
                        "payment.checkout.create",
                        "social.post.publish",
                        "local.business.profile.update",
                    ]
                }
            )
        }
    )
    engine = PolicyEngine(policy=policy, tenant_id=BOR_SLUG)
    monkeypatch.setattr(engine, "_tenant", lambda _tid: tenant)
    return engine


@pytest.mark.parametrize(
    "cap",
    [
        "web.search",
        "web.page.extract",
        "web.seo.audit",
        "data.lead.validate",
        "crm.contact.create",
        "crm.deal.create",
        "calendar.event.create",
        "calendar.event.read",
    ],
)
def test_policy_allows_automatic(monkeypatch: pytest.MonkeyPatch, cap: str) -> None:
    assert _engine_with_tenant(monkeypatch).decide(BOR_SLUG, cap).effect == "allow"


@pytest.mark.parametrize(
    "cap",
    [
        "whatsapp.message.send",
        "whatsapp.template.send",
        "payment.link.create",
        "payment.checkout.create",
        "social.post.publish",
    ],
)
def test_policy_requires_approval(monkeypatch: pytest.MonkeyPatch, cap: str) -> None:
    engine = _engine_with_tenant(monkeypatch)
    decision = engine.decide(BOR_SLUG, cap, roles=["director"])
    assert decision.effect == "require_approval"


def test_policy_denies_unknown(monkeypatch: pytest.MonkeyPatch) -> None:
    assert _engine_with_tenant(monkeypatch).decide(BOR_SLUG, "crm.contact.delete").effect == "deny"
