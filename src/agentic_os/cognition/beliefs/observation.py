from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from ...kernel.types.time import now_utc
from ...kernel.types.ids import new_id

class Observation(BaseModel):
    """Hecho bruto entrante. Nunca se confia 100%. Pasa por proposicion -> belief."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(default_factory=new_id)
    source: str = Field(description="gmail, slack, web_scrape, user, pipeline...")
    kind: str = Field(default="raw", description="email, message, document, event...")
    data: Dict[str, Any]
    trust: float = Field(default=0.8, ge=0.0, le=1.0, description="confianza de la fuente")
    tenant_id: str = Field(default="system")
    correlation_id: Optional[str] = None
    at: datetime = Field(default_factory=now_utc)

    @field_validator("source")
    @classmethod
    def _source_nonblank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Observation.source obligatorio")
        return v.strip().lower()

    def to_belief_dict(self) -> Dict[str, Any]:
        return {
            "source_observation_id": self.id,
            "content": self.data,
            "confidence": self.trust,
        }
