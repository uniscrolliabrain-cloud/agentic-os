from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from ...kernel.types.time import now_utc
from ...kernel.types.ids import new_id

class BeliefKind(str, Enum):
    FACT = "fact"
    INFERRED = "inferred"
    ASSUMPTION = "assumption"
    GOAL = "goal"
    CONSTRAINT = "constraint"
    PREFERENCE = "preference"
    OBSERVATION = "observation"

class Belief(BaseModel):
    """Unidad de conocimiento auditada. Inmutable, con confianza y procedencia."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(default_factory=new_id)
    kind: str = Field(
        default=BeliefKind.FACT.value,
        description="clase de conocimiento (canonico o libre; el proposer/LLM puede proponer kinds propios del dominio)",
    )
    key: Optional[str] = Field(default=None, description="clave estable ej. cliente.email, empresa.nombre")
    content: Dict[str, Any]
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    source_observation_id: Optional[str] = None
    source_agent_id: Optional[str] = None
    supports: List[str] = Field(default_factory=list, description="ids de beliefs que apoyan esta")
    contradicts: List[str] = Field(default_factory=list, description="ids de beliefs que contradicen esta")
    expires_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)

    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return now_utc() > self.expires_at

    def with_confidence(self, new_conf: float, supporting_id: Optional[str] = None) -> "Belief":
        data = self.model_dump()
        data["confidence"] = max(0.0, min(1.0, new_conf))
        data["updated_at"] = now_utc()
        if supporting_id:
            supports = list(data.get("supports", []))
            if supporting_id not in supports:
                supports.append(supporting_id)
            data["supports"] = supports
        return Belief(**data)

    def decayed(self, factor: float = 0.95) -> "Belief":
        return self.with_confidence(self.confidence * factor)
