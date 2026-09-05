"""Test A5 — ENTITY_TYPE_REGISTRY.

Valida:
- Registro contiene los 9 tipos de entidad.
- entity_from_payload crea la instancia correcta.
- Kind desconocido -> UnknownEntityTypeError (fail-closed).
- Payload invalido -> ValidationError.
- Integridad del registro (clave == kind de la clase).
"""
import pytest
from pydantic import ValidationError

from agentic_os.kernel.ontology.domain_models import (
    ENTITY_TYPE_REGISTRY,
    Lead,
    Proposal,
    Brand,
    Campaign,
    BlogPost,
    CoachingClient,
    SessionNote,
    TherapyClient,
    Appointment,
    UnknownEntityTypeError,
    entity_from_payload,
    validate_registry_integrity,
)


def test_registry_contains_9_types():
    assert len(ENTITY_TYPE_REGISTRY) == 9


def test_registry_kinds_are_canonical():
    expected = {
        "marketing.lead": Lead,
        "marketing.proposal": Proposal,
        "marketing.brand": Brand,
        "marketing.campaign": Campaign,
        "content.blog_post": BlogPost,
        "coaching.client": CoachingClient,
        "coaching.session_note": SessionNote,
        "therapy.client": TherapyClient,
        "therapy.appointment": Appointment,
    }
    assert ENTITY_TYPE_REGISTRY == expected


def test_registry_integrity_passes():
    validate_registry_integrity()


def test_entity_from_payload_creates_lead():
    entity = entity_from_payload(
        "marketing.lead",
        {"tenant_id": "t1", "name": "Juan", "email": "j@t.com"},
    )
    assert isinstance(entity, Lead)


def test_entity_from_payload_creates_appointment():
    from datetime import datetime, timezone
    entity = entity_from_payload(
        "therapy.appointment",
        {
            "tenant_id": "t1",
            "client_id": "c1",
            "scheduled_at": datetime.now(timezone.utc),
        },
    )
    assert isinstance(entity, Appointment)


def test_entity_from_payload_unknown_kind_fails():
    with pytest.raises(UnknownEntityTypeError):
        entity_from_payload("tipo.inexistente", {"tenant_id": "t1"})


def test_entity_from_payload_invalid_payload_fails():
    with pytest.raises(Exception):
        entity_from_payload(
            "marketing.lead",
            {"tenant_id": "t1", "name": "Juan", "email": "sin-arroba"},
        )