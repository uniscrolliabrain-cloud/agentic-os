"""Test A1 — DomainEntity base.

Valida:
- DomainEntity se importa desde kernel.ontology.domain_models.
- Instanciar sin tenant_id debe fallar con ValidationError.
- Usa now_utc() (nunca datetime.utcnow()).
- frozen=True (inmutable).
- extra='forbid' (rechaza campos inesperados).
- Version no negativa.
"""
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from agentic_os.kernel.ontology.domain_models import DomainEntity, BaseDomainModel
from agentic_os.kernel.types.time import now_utc


def test_domain_entity_importable():
    assert DomainEntity is BaseDomainModel


def test_domain_entity_requires_tenant_id():
    with pytest.raises(ValidationError) as exc:
        DomainEntity(entity_type="dummy")
    assert "tenant_id" in str(exc.value).lower()


def test_domain_entity_requires_entity_type():
    with pytest.raises(ValidationError) as exc:
        DomainEntity(tenant_id="tenant_1")
    assert "entity_type" in str(exc.value).lower()


def test_domain_entity_uses_now_utc():
    entity = DomainEntity(entity_type="dummy", tenant_id="tenant_1")
    assert entity.created_at.tzinfo is not None
    assert entity.created_at.tzinfo.utcoffset(entity.created_at) == timezone.utc.utcoffset(datetime.now(timezone.utc))


def test_domain_entity_is_frozen():
    entity = DomainEntity(entity_type="dummy", tenant_id="tenant_1")
    with pytest.raises((TypeError, ValueError)):
        entity.id = "nuevo-id"


def test_domain_entity_rejects_extra_fields():
    with pytest.raises(ValidationError):
        DomainEntity(entity_type="dummy", tenant_id="tenant_1", campo_extra="valor")


def test_domain_entity_rejects_negative_version():
    with pytest.raises(ValidationError):
        DomainEntity(entity_type="dummy", tenant_id="tenant_1", version=-1)


# --- A2-A4: Entidades concretas ---

def test_lead_creates_with_valid_data():
    from agentic_os.kernel.ontology.domain_models import Lead
    lead = Lead(tenant_id="t1", name="Juan", email="juan@test.com")
    assert lead.kind == "marketing.lead"


def test_lead_rejects_invalid_email():
    from agentic_os.kernel.ontology.domain_models import Lead
    with pytest.raises(ValidationError):
        Lead(tenant_id="t1", name="Juan", email="sin-arroba")


def test_proposal_rejects_empty_lead_id():
    from agentic_os.kernel.ontology.domain_models import Proposal
    with pytest.raises(ValidationError):
        Proposal(tenant_id="t1", lead_id="", amount=1000.0)


def test_proposal_rejects_negative_amount():
    from agentic_os.kernel.ontology.domain_models import Proposal
    with pytest.raises(ValidationError):
        Proposal(tenant_id="t1", lead_id="lead_1", amount=-100.0)


def test_campaign_rejects_empty_brand_id():
    from agentic_os.kernel.ontology.domain_models import Campaign
    with pytest.raises(ValidationError):
        Campaign(tenant_id="t1", name="Camp 1", brand_id="", budget=5000.0)


def test_brand_allows_optional_website():
    from agentic_os.kernel.ontology.domain_models import Brand
    brand = Brand(tenant_id="t1", name="MyBrand")
    assert brand.website is None


def test_blogpost_rejects_empty_title():
    from agentic_os.kernel.ontology.domain_models import BlogPost
    with pytest.raises(ValidationError):
        BlogPost(tenant_id="t1", title="", body="contenido")


def test_coaching_client_rejects_invalid_email():
    from agentic_os.kernel.ontology.domain_models import CoachingClient
    with pytest.raises(ValidationError):
        CoachingClient(tenant_id="t1", name="Cliente", email="bad-email")


def test_session_note_rejects_empty_client_id():
    from agentic_os.kernel.ontology.domain_models import SessionNote
    with pytest.raises(ValidationError):
        SessionNote(tenant_id="t1", client_id="", notes="nota")


def test_therapy_client_creates_with_kind():
    from agentic_os.kernel.ontology.domain_models import TherapyClient
    client = TherapyClient(tenant_id="t1", name="Paciente", specialty="ansiedad")
    assert client.kind == "therapy.client"


def test_appointment_rejects_empty_client_id():
    from datetime import datetime, timezone
    from agentic_os.kernel.ontology.domain_models import Appointment
    with pytest.raises(ValidationError):
        Appointment(
            tenant_id="t1",
            client_id="",
            scheduled_at=datetime.now(timezone.utc),
        )
