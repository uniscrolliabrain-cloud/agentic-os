from __future__ import annotations
import re
from pydantic import BaseModel, Field, ConfigDict, field_validator, ValidationInfo
from ..types.ids import new_id
from .vocabulary import is_canonical_relation_kind
from ..types.time import now_utc
from datetime import datetime

_KIND_RE = re.compile(r"[a-z][a-z0-9_-]*")


class Relation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    id: str = Field(default_factory=new_id)
    kind: str
    src_id: str
    dst_id: str
    attributes: dict[str, object] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=now_utc)

    @field_validator("kind")
    @classmethod
    def _kind_canonico(cls, v: str) -> str:
        """Slug canonico (validado por is_canonical_relation_kind del
        vocabulary del kernel, AUD-14: una sola definicion). La pertenencia
        al Vocabulary la valida OntologyValidator."""
        if not v or not is_canonical_relation_kind(v):
            raise ValueError(
                f"Relation.kind invalido: {v!r} (usar slug minusculas: 'uses'...)"
            )
        return v

    @field_validator("src_id", "dst_id")
    @classmethod
    def _ids_no_vacios(cls, v: str) -> str:
        if not v:
            raise ValueError("Relation.src_id/dst_id no pueden estar vacíos")
        return v

    @field_validator("dst_id")
    @classmethod
    def _sin_auto_relacion(cls, v: str, info: ValidationInfo) -> str:
        src = info.data.get("src_id")
        if src is not None and v == src:
            raise ValueError(
                "Relation con src_id == dst_id (auto-relación) no permitida"
            )
        return v

