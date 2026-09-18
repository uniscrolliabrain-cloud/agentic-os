"""16 action verbs del metamodelo (spec 04, D04).

Los verbos son universales (kernel), no de dominio. Toda MicroActionSchema
debe declarar `action_type` en este enum. Combinaciones logicas se expresan
como pipelines, nunca como "acciones hibridas".

Pares prohibidos por defecto (spec 04): `(Delete, Person)` y equivalentes.
Una capability explicita puede permitir el par, pero el default es deny.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict


ActionType = Literal[
    "Discover",
    "Search",
    "Retrieve",
    "Read",
    "Write",
    "Create",
    "Transform",
    "Analyze",
    "Classify",
    "Validate",
    "Communicate",
    "Publish",
    "Execute",
    "Update",
    "Delete",
    "Monitor",
]


class ActionTypeEnum(BaseModel):
    """Fuente de verdad como modelo, por si se necesita introspeccion."""

    model_config = ConfigDict(frozen=True, extra="forbid")


ACTION_TYPES: tuple[str, ...] = (
    "Discover", "Search", "Retrieve", "Read", "Write", "Create",
    "Transform", "Analyze", "Classify", "Validate", "Communicate",
    "Publish", "Execute", "Update", "Delete", "Monitor",
)

assert len(ACTION_TYPES) == 16, "spec 04 declara exactamente 16 verbos"
assert len(set(ACTION_TYPES)) == 16, "verbos unicos"


# Pares (Action, Entity) prohibidos por defecto.
# "Entity" aqui es el nombre del tipo en spec 03 sin prefijo core.
# Una capability explicita puede permitirlos; el default es deny.
FORBIDDEN_ACTION_ENTITY_PAIRS: frozenset[tuple[str, str]] = frozenset({
    ("Delete", "Person"),
    ("Delete", "Organization"),
    ("Delete", "Company"),
    ("Delete", "Email"),
    ("Delete", "Message"),
    ("Delete", "Event"),
    ("Publish", "Person"),
    ("Publish", "Email"),
    ("Publish", "Message"),
})


def is_valid_action(action: str) -> bool:
    """True si el verbo esta en el catalogo."""
    return action in ACTION_TYPES


def is_forbidden_pair(action: str, entity_type: str) -> bool:
    """True si el par (action, entity) esta prohibido por defecto.

    Acepta `entity_type` con o sin prefijo `core.`.
    """
    entity_short = entity_type.split(".", 1)[1] if entity_type.startswith("core.") else entity_type
    normalized = entity_short.replace("_", " ").title().replace(" ", "")
    return (action, normalized) in FORBIDDEN_ACTION_ENTITY_PAIRS


__all__ = [
    "ActionType",
    "ActionTypeEnum",
    "ACTION_TYPES",
    "FORBIDDEN_ACTION_ENTITY_PAIRS",
    "is_valid_action",
    "is_forbidden_pair",
]

