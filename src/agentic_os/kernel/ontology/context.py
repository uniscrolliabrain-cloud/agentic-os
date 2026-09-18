"""Context del metamodelo (spec 01): 8 categorias."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import Field, field_validator

from ..types import KernelModel
from ..types.ids import new_id


CONTEXT_CATEGORIES: tuple[str, ...] = (
    "User", "Client", "Project", "Brand", "Campaign", "Goal",
    "Constraint", "Permission",
)

assert len(CONTEXT_CATEGORIES) == 8, "spec 01 declara 8 categorias de Context"


class ContextEntry(KernelModel):
    id: str = Field(default_factory=new_id)
    tenant_id: str
    category: str
    entity_id: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("category")
    @classmethod
    def _category_valida(cls, v: str) -> str:
        if v not in CONTEXT_CATEGORIES:
            raise ValueError(f"category invalida: {v!r}")
        return v

    @field_validator("tenant_id")
    @classmethod
    def _tenant_no_vacio(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("tenant_id es obligatorio")
        return v


class Context(KernelModel):
    tenant_id: str
    entries: List[ContextEntry] = Field(default_factory=list)

    def by_category(self, category: str) -> List[ContextEntry]:
        return [e for e in self.entries if e.category == category]

    def has(self, category: str) -> bool:
        return any(e.category == category for e in self.entries)

    def add(self, category: str, payload: Optional[Dict[str, Any]] = None,
            entity_id: Optional[str] = None) -> ContextEntry:
        entry = ContextEntry(
            tenant_id=self.tenant_id, category=category,
            entity_id=entity_id, payload=payload or {},
        )
        self.entries.append(entry)
        return entry


__all__ = ["CONTEXT_CATEGORIES", "ContextEntry", "Context"]

