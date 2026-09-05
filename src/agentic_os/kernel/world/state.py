from __future__ import annotations
from pydantic import BaseModel, Field, field_validator
from typing import Dict, Any


class WorldState(BaseModel):
    """Estado del mundo derivado del EventLog.

    Las entidades y relations usan Dict[str, Any] por flexibilidad de dominio,
    pero se valida que sean dicts (no listas, strings, etc).
    """
    entities: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    relations: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    version: int = 0

    @field_validator("entities", "relations")
    @classmethod
    def _validate_is_dict(cls, v: Any) -> Dict[str, Any]:
        if not isinstance(v, dict):
            raise ValueError(f"Debe ser un dict, no {type(v).__name__}")
        return v

    @field_validator("version")
    @classmethod
    def _validate_version(cls, v: int) -> int:
        if v < 0:
            raise ValueError("version no puede ser negativa")
        return v
