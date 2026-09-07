from __future__ import annotations
from typing import Annotated, Any, Dict, Union

from pydantic import BaseModel, Field, field_validator, model_validator

from ..ontology.domain_models import (
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


# A6: Union discriminada de las 9 entidades tipadas del Bloque A.
# Unicamente entidades registradas pueden habitar el WorldState (fail-closed).
EntityUnion = Annotated[
    Union[
        Lead,
        Proposal,
        Brand,
        Campaign,
        BlogPost,
        CoachingClient,
        SessionNote,
        TherapyClient,
        Appointment,
    ],
    Field(discriminator="kind"),
]


class WorldState(BaseModel):
    """Estado del mundo derivado del EventLog.

    A6: entities ahora es Dict[str, EntityUnion] — solo acepta instancias de
    las 9 entidades tipadas, discriminadas por su campo kind. Ya no acepta
    dicts sueltos ni payloads sin validar (cierra el bug de Pydantico falso).

    relations permanece como Dict[str, Dict[str, Any]] hasta migrar
    relations.py a modelos tipados.
    """

    entities: Dict[str, EntityUnion] = Field(default_factory=dict)
    relations: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    version: int = 0

    @model_validator(mode="after")
    def _keys_match_entity_ids(self) -> "WorldState":
        """Fail-closed: la clave del dict debe coincidir con entity.id."""
        for key, entity in self.entities.items():
            if key != entity.id:
                raise ValueError(
                    f"Clave '{key}' no coincide con entity.id '{entity.id}'"
                )
        return self

    @field_validator("relations")
    @classmethod
    def _validate_relations_is_dict(cls, v: Any) -> Dict[str, Any]:
        if not isinstance(v, dict):
            raise ValueError(f"Debe ser un dict, no {type(v).__name__}")
        return v

    @field_validator("version")
    @classmethod
    def _validate_version(cls, v: int) -> int:
        if v < 0:
            raise ValueError("version no puede ser negativa")
        return v