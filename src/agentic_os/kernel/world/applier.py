from __future__ import annotations

from typing import Any

from .events import Event
from .state import EntityUnion, WorldState
from ..ontology.domain_models import entity_from_payload, UnknownEntityTypeError


class InvalidEntityEventError(ValueError):
    """Evento de entidad invalido (fail-closed, nunca se ignora en silencio)."""


def apply(state: WorldState, event: Event[Any]) -> WorldState:
    """Aplica un evento al WorldState (funcion pura).

    A6/A7: entity_created y entity_updated usan event.data tipado.
    Acepta legacy event.payload (dict) para compatibilidad y lo convierte.
    Si la validacion falla, se lanza excepcion y el estado original
    NO se modifica (semantica transaccional).
    """
    new_entities = dict(state.entities)
    new_relations = dict(state.relations)
    if event.kind == "entity_created":
        if event.data is not None:
            entity = event.data
        else:
            payload = dict(event.payload or {})
            kind = (
                payload.pop("kind", None)
                or payload.pop("entity_type", None)
                or event.kind
            )
            if not kind:
                raise InvalidEntityEventError(
                    f"entity_created sin kind/entity_type registrado "
                    f"(entity_id={event.entity_id})"
                )
            payload.setdefault("id", event.entity_id)
            payload.setdefault("tenant_id", event.tenant_id)
            try:
                entity = entity_from_payload(kind, payload)
            except UnknownEntityTypeError as e:
                raise InvalidEntityEventError(str(e)) from e
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
        if event.data is not None:
            updated = event.data
        else:
            merged = existing.model_dump()
            merged.update(event.payload or {})
            updated = type(existing)(**merged)
        if updated.id != event.entity_id:
            raise InvalidEntityEventError(
                f"entity_updated: id del payload '{updated.id}' != "
                f"entity_id del evento '{event.entity_id}'"
            )
        new_entities[event.entity_id] = updated
    elif event.kind == "relation_created":
        new_relations[event.entity_id] = event.payload or {}
    elif event.kind == "relation_deleted":
        new_relations.pop(event.entity_id, None)
    return WorldState(
        entities=new_entities, relations=new_relations, version=state.version + 1
    )