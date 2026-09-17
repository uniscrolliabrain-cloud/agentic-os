"""Bug 8 - Pydantic falso en WorldState: AHORA CORREGIDO con A6.

WorldState.entities es Dict[str, EntityUnion] (Union discriminada por kind).
Estos tests afirman el comportamiento CORREGIDO:
- Payloads invalidos son rechazados con ValidationError.
- Entidades validas se almacenan tipadas (instancias de su clase).
- Kinds no registrados son rechazados.
"""

import pytest
from pydantic import ValidationError

from agentic_os.kernel.world.state import WorldState
from agentic_os.kernel.world.applier import apply, InvalidEntityEventError
from agentic_os.kernel.world.events import Event, EventLog
from agentic_os.kernel.ontology.domain_models import Lead, Proposal


def _lead_payload(entity_id: str = "person_1") -> dict:
    return {
        "kind": "marketing.lead",
        "id": entity_id,
        "tenant_id": "test-tenant",
        "name": "Juan",
        "email": "juan@test.com",
    }


def test_worldstate_rejects_invalid_entity_payloads():
    """WorldState ya NO acepta dicts sueltos: age='gato' y similares fallan."""
    with pytest.raises(ValidationError):
        WorldState(entities={"person_1": {"name": "Juan", "age": "gato"}})


def test_worldstate_accepts_valid_typed_entities():
    """Entidades validas se almacenan como instancias tipadas."""
    state = WorldState(entities={"person_1": Lead(**_lead_payload())})
    entity = state.entities["person_1"]
    assert isinstance(entity, Lead)
    assert entity.name == "Juan"
    assert entity.kind == "marketing.lead"


def test_worldstate_rejects_unknown_kind():
    """Un kind no registrado en ENTITY_TYPE_REGISTRY es rechazado."""
    with pytest.raises(ValidationError):
        WorldState(
            entities={"person_1": {"kind": "tipo.inexistente", "tenant_id": "t1"}}
        )


def test_worldstate_entities_are_typed_union():
    """La anotacion de entities ya no es Dict[str, Any]."""
    annotation = WorldState.model_fields["entities"].annotation
    type_str = str(annotation)
    assert "Lead" in type_str and "typing.Any" not in type_str, (
        f"WorldState.entities debe ser Union de entidades tipadas, no {type_str}"
    )


def test_worldstate_rejects_non_dict_entities():
    with pytest.raises(ValidationError):
        WorldState(entities="not_a_dict")


def test_apply_rejects_invalid_payload_transactionally():
    """apply() con payload invalido lanza y NO modifica el estado original."""
    log = EventLog()
    log.append(
        Event(
            kind="entity_created",
            entity_id="prop_1",
            tenant_id="test-tenant",
            payload={
                "kind": "marketing.proposal",
                "id": "prop_1",
                "lead_id": "lead_1",
                "amount": 100.0,
            },
        )
    )
    state = WorldState()
    state = apply(state, log.all_events()[0])
    assert isinstance(state.entities["prop_1"], Proposal)

    # Evento corrupto: amount no puede ser negativo
    bad = Event(
        kind="entity_updated",
        entity_id="prop_1",
        tenant_id="test-tenant",
        payload={"amount": -5.0},
    )
    with pytest.raises(ValidationError):
        apply(state, bad)
    # Semantica transaccional: el estado original queda intacto
    assert state.entities["prop_1"].amount == 100.0
    assert state.version == 1


def test_apply_rejects_entity_created_without_kind():
    event = Event(
        kind="entity_created",
        entity_id="e1",
        tenant_id="test-tenant",
        payload={"name": "sin kind"},
    )
    with pytest.raises(InvalidEntityEventError):
        apply(WorldState(), event)


def test_apply_rejects_update_on_missing_entity():
    event = Event(
        kind="entity_updated",
        entity_id="fantasma",
        tenant_id="test-tenant",
        payload={"status": "gone"},
    )
    with pytest.raises(InvalidEntityEventError):
        apply(WorldState(), event)


def test_apply_updates_entity_typed():
    state = WorldState()
    created = Event(
        kind="entity_created",
        entity_id="l1",
        tenant_id="test-tenant",
        payload={"kind": "marketing.lead", "name": "Ana", "email": "ana@x.com"},
    )
    state = apply(state, created)
    updated = Event(
        kind="entity_updated",
        entity_id="l1",
        tenant_id="test-tenant",
        payload={"status": "qualified"},
    )
    state2 = apply(state, updated)
    assert state2.entities["l1"].status == "qualified"
    assert state2.version == 2