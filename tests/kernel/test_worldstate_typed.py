"""Tests A6 + A8 — WorldState tipado y replay fail-closed.

A6: entities es Dict[str, EntityUnion] (Union discriminada por kind),
con invariante clave == entity.id.
A8: replay() lanza CorruptEventError con el indice del evento corrupto,
nunca devuelve un estado parcial.
"""

import pytest
from pydantic import ValidationError

from agentic_os.kernel.world.events import Event, EventLog
from agentic_os.kernel.world.replay import replay, CorruptEventError
from agentic_os.kernel.world.state import WorldState, EntityUnion
from agentic_os.kernel.world.applier import apply, InvalidEntityEventError
from agentic_os.kernel.ontology.domain_models import (
    Lead,
    Proposal,
    Brand,
    Campaign,
    BlogPost,
    CoachingClient,
    SessionNote,
    TherapyClient,
    Appointment,
)


def _valid_lead(entity_id: str = "l1", tenant: str = "t1") -> Lead:
    return Lead(id=entity_id, tenant_id=tenant, name="Ana", email="ana@t.com")


# ------------------------------------------------------------- A6 -----------

def test_worldstate_typed_entities_accepted():
    lead = _valid_lead()
    state = WorldState(entities={"l1": lead})
    assert isinstance(state.entities["l1"], Lead)


def test_worldstate_all_nine_entities_accepted():
    from datetime import datetime, timezone

    fixtures = {
        "l": Lead(tenant_id="t", name="A", email="a@t.com"),
        "p": Proposal(tenant_id="t", lead_id="l", amount=10.0),
        "b": Brand(tenant_id="t", name="Marca"),
        "c": Campaign(tenant_id="t", name="Camp", brand_id="b", budget=100.0),
        "bp": BlogPost(tenant_id="t", title="Hola", body="Contenido"),
        "cc": CoachingClient(tenant_id="t", name="C", email="c@t.com"),
        "sn": SessionNote(tenant_id="t", client_id="cc", content="x"),
        "tc": TherapyClient(tenant_id="t", name="T"),
        "ap": Appointment(
            tenant_id="t", client_id="tc", scheduled_at=datetime.now(timezone.utc)
        ),
    }
    state = WorldState(entities=fixtures)
    assert len(state.entities) == 9
    for value in state.entities.values():
        assert hasattr(value, "kind")
        assert hasattr(value, "entity_type")


def test_worldstate_rejects_key_not_matching_id():
    lead = Lead(tenant_id="t", name="A", email="a@t.com")
    with pytest.raises(ValidationError, match="no coincide"):
        WorldState(entities={"clave-incorrecta": lead})


def test_worldstate_rejects_unregistered_dict_payload():
    with pytest.raises(ValidationError):
        WorldState(entities={"x": {"name": "dict suelto", "age": "gato"}})


def test_worldstate_rejects_non_dict_entities():
    with pytest.raises(ValidationError):
        WorldState(entities=["no", "soy", "dict"])


# ------------------------------------------------------------- A8 -----------

def _clean_log() -> EventLog:
    log = EventLog()
    log.append(
        Event(
            kind="entity_created",
            entity_id="l1",
            tenant_id="t1",
            payload={"kind": "marketing.lead", "name": "Ana", "email": "ana@t.com"},
        )
    )
    log.append(
        Event(
            kind="entity_created",
            entity_id="p1",
            tenant_id="t1",
            payload={"kind": "marketing.proposal", "lead_id": "l1", "amount": 50.0},
        )
    )
    return log


def test_replay_rebuilds_typed_state_from_clean_log():
    state = replay(_clean_log())
    assert state.version == 2
    assert isinstance(state.entities["l1"], Lead)
    assert isinstance(state.entities["p1"], Proposal)


def test_replay_raises_with_index_of_corrupt_event():
    log = _clean_log()
    # Evento corrupto en indice 2: payload invalido para su kind
    log.append(
        Event(
            kind="entity_created",
            entity_id="c1",
            tenant_id="t1",
            payload={"kind": "marketing.campaign", "budget": -1.0},
        )
    )
    with pytest.raises(CorruptEventError) as exc_info:
        replay(log)
    assert exc_info.value.index == 2
    assert exc_info.value.kind == "entity_created"


def test_replay_never_returns_partial_state():
    """El estado previo al fallo NO se devuelve: replay o es limpio o falla."""
    log = _clean_log()
    log.append(
        Event(
            kind="entity_updated",
            entity_id="inexistente",
            tenant_id="t1",
            payload={"status": "x"},
        )
    )
    with pytest.raises(CorruptEventError) as exc_info:
        replay(log)
    assert exc_info.value.index == 2


def test_apply_is_pure_on_failure():
    state = WorldState(entities={"l1": _valid_lead()})
    bad = Event(
        kind="entity_updated",
        entity_id="l1",
        tenant_id="t1",
        payload={"email": "email-invalido-sin-arroba"},
    )
    with pytest.raises(ValidationError):
        apply(state, bad)
    # Purity: el estado original no cambio
    assert state.entities["l1"].email == "ana@t.com"
    assert state.version == 0