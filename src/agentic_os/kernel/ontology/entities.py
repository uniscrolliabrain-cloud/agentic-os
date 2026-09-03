from __future__ import annotations
import re
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Any
from ..types.ids import new_id
from ..types.time import now_utc
from datetime import datetime

_KIND_RE = re.compile(r"[a-z][a-z0-9_-]*")


class Entity(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str = Field(default_factory=new_id)
    kind: str
    attributes: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=now_utc)

    @field_validator("id")
    @classmethod
    def _id_no_vacio(cls, v: str) -> str:
        if not v:
            raise ValueError("Entity.id no puede estar vacío")
        return v

    @field_validator("kind")
    @classmethod
    def _kind_canonico(cls, v: str) -> str:
        """kind debe ser un slug canónico (la pertenencia al Vocabulary la
        valida OntologyValidator, determinista; aquí solo se garantiza forma)."""
        if not v or not _KIND_RE.fullmatch(v):
            raise ValueError(
                f"Entity.kind inválido: {v!r} (usar slug minúsculas: 'actor', 'tool'...)"
            )
        return v

    @field_validator("attributes")
    @classmethod
    def _attrs_claves_str(cls, v: dict[str, Any]) -> dict[str, Any]:
        for key in v:
            if not isinstance(key, str):
                raise ValueError("Entity.attributes debe tener claves str")
        return v

