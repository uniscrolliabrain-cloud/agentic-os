"""MissionMemory (spec 15). Reconstruible del EventLog. Vive en kernel."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..types.ids import new_id


class EventRef(BaseModel):
    """Referencia a un evento del EventLog (trazabilidad)."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    event_id: str
    kind: str
    tenant_id: str


class Fact(BaseModel):
    """Afirmacion validada, con fuente obligatoria."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(default_factory=new_id)
    statement: str
    source: str
    confidence: float = 1.0

    @field_validator("statement", "source")
    @classmethod
    def _nonblank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("statement/source obligatorio")
        return v


class MissionMemory(BaseModel):
    """Memoria de una mision (TaskPlan ejecutado).

    - plan_id: TaskPlan.id
    - tenant_id: tenant propietario
    - context: node_id -> output (para handoffs)
    - facts: afirmaciones validadas (con fuente)
    - history: refs a los eventos del EventLog
    """
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(default_factory=new_id)
    plan_id: str
    tenant_id: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    facts: List[Fact] = Field(default_factory=list)
    history: List[EventRef] = Field(default_factory=list)

    @field_validator("plan_id")
    @classmethod
    def _plan_no_vacio(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("plan_id obligatorio")
        return v

    def with_node_output(self, node_id: str, output: Any) -> "MissionMemory":
        ctx = dict(self.context)
        ctx[node_id] = output
        return self.model_copy(update={"context": ctx})

    def with_fact(self, statement: str, source: str, confidence: float = 1.0) -> "MissionMemory":
        new_facts = list(self.facts) + [Fact(statement=statement, source=source, confidence=confidence)]
        return self.model_copy(update={"facts": new_facts})

    def with_event(self, event_id: str, kind: str, tenant_id: str) -> "MissionMemory":
        new_hist = list(self.history) + [EventRef(event_id=event_id, kind=kind, tenant_id=tenant_id)]
        return self.model_copy(update={"history": new_hist})


__all__ = ["EventRef", "Fact", "MissionMemory"]

