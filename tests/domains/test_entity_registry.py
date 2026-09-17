"""Test A5 - ENTITY_TYPE_REGISTRY del kernel (v3).

El kernel ARRANCA con el registro VACIO. Las 9 entidades "de juguete" viven
en `domains/_examples/` y se registran explicitamente via
`register_demo_entities()`.
"""
from __future__ import annotations

import pytest

from agentic_os.domains._examples import (
    Appointment,
    BlogPost,
    Brand,
    Campaign,
    CoachingClient,
    Lead,
    Proposal,
    SessionNote,
    TherapyClient,
    register_demo_entities,
)
from agentic_os.kernel.ontology.domain_models import (
    ENTITY_TYPE_REGISTRY,
    UnknownEntityTypeError,
    entity_from_payload,
    validate_registry_integrity,
)

DEMO_REGISTRY = {
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


def test_kernel_registry_starts_empty():
    assert ENTITY_TYPE_REGISTRY == {}, (
        f"el kernel trae entidades preinstaladas: {list(ENTITY_TYPE_REGISTRY)}"
    )


def test_register_demo_entities_puebla_registry():
    register_demo_entities()
    assert len(ENTITY_TYPE_REGISTRY) == 9
    for kind, cls in DEMO_REGISTRY.items():
        assert ENTITY_TYPE_REGISTRY.get(kind) is cls


def test_registry_integrity_passes_after_register():
    register_demo_entities()
    validate_registry_integrity()


def test_entity_from_payload_creates_lead():
    register_demo_entities()
    entity = entity_from_payload("marketing.lead",
                                 {"tenant_id": "t1", "name": "Juan",
                                  "email": "j@t.com"})
    assert isinstance(entity, Lead)


def test_entity_from_payload_unknown_kind_fails():
    with pytest.raises(UnknownEntityTypeError):
        entity_from_payload("tipo.inexistente", {"tenant_id": "t1"})