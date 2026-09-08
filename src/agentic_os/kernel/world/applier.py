from __future__ import annotations

from .events import Event, EventPayload
from .state import WorldState
from ..ontology.domain_models import entity_from_payload

_BASE_PAYLOAD_FIELDS = {"status", "error", "error_type", "params", "output_keys"}


class InvalidEntityEventError(ValueError):
    """Evento de entidad invalido (fail-closed, nunca se ignora en silencio)."""


def _payload_dict(payload: EventPayload) -> dict:
    """Convierte el payload a dict con los campos de entidad (sin campos base)."""
    data = payload.model_dump()
    # Eliminar campos base de EventPayload que no son datos de entidad
    for field in _BASE_PAYLOAD_FIELDS:
        data.pop(field, None)
    return data


def apply(state: WorldState, event: Event) -> WorldState:
    """Aplica un evento al WorldState (funcion pura).

    A6/A7: entity_created y entity_updated resuelven el tipo desde
    ENTITY_TYPE_REGISTRY y validan el payload ANTES de construir el nuevo
    estado. Si la validacion falla, se lanza excepcion y el estado original
    NO se modifica (semantica transaccional).
    """
    new_entities = dict(state.entities)
    new_relations = dict(state.relations)
    if event.kind == "entity_created":
        kind = event.payload.kind or event.payload.entity_type
        if not kind:
            raise InvalidEntityEventError(
                f"entity_created sin kind/entity_type registrado "
                f"(entity_id={event.entity_id})"
            )
        data = _payload_dict(event.payload)
        # Normalizacion legitima: el evento declara identidad y tenant.
        data.setdefault("id", event.entity_id)
        data.setdefault("tenant_id", event.tenant_id)
        entity = entity_from_payload(kind, data)
        if entity.id != event.entity_id:
            raise InvalidEntityEventError(
                f"entity_created: id del payload '{entity.id}' != "
                f"entity_id del evento '{event.entity_id}'"
            )
        new_entities[event.entity_id] = entity
    elif event.kind == "entity_updated":
        existing = new_entities.get(event.entity_id)
        if existing is None:
            raise InvalidEntityEventError(
                f"entity_updated sobre entidad inexistente "
                f"'{event.entity_id}' (fail-closed)"
            )
        merged = existing.model_dump()
        merged.update(_payload_dict(event.payload))
        updated = type(existing)(**merged)
        new_entities[event.entity_id] = updated
    elif event.kind == "entity_deleted":
        new_entities.pop(event.entity_id, None)
    elif event.kind == "relation_created":
        new_relations[event.entity_id] = _payload_dict(event.payload)
    elif event.kind == "relation_deleted":
        new_relations.pop(event.entity_id, None)
    return WorldState(
        entities=new_entities, relations=new_relations, version=state.version + 1
    )