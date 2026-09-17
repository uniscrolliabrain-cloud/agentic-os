"""Estado del mundo derivado del EventLog."""
from __future__ import annotations

from typing import Any, Dict

from pydantic import BaseModel, Field, field_validator, model_validator

from ..ontology.domain_models import BaseDomainModel


class WorldState(BaseModel):
    """Estado del mundo derivado del EventLog."""

    entities: Dict[str, BaseDomainModel] = Field(default_factory=dict)
    relations: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    version: int = 0

    @field_validator("entities")
    @classmethod
    def _entities_are_domain_models(cls, v: Any) -> Dict[str, BaseDomainModel]:
        if not isinstance(v, dict):
            raise ValueError(f"entities debe ser dict, no {type(v).__name__}")
        for key, entity in v.items():
            if not isinstance(entity, BaseDomainModel):
                raise ValueError(
                    f"entities[{key!r}] no es BaseDomainModel: "
                    f"{type(entity).__name__}"
                )
        return v

    @model_validator(mode="after")
    def _keys_match_entity_ids(self) -> "WorldState":
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
            raise ValueError(f"relations debe ser dict, no {type(v).__name__}")
        return v

    @field_validator("version")
    @classmethod
    def _validate_version(cls, v: int) -> int:
        if v < 0:
            raise ValueError("version no puede ser negativa")
        return v
