"""cognition.memory.models: las 4 memorias persistentes tipadas."""
from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from ...kernel.types.time import now_utc
from ...kernel.types.ids import new_id

class WorkingItem(BaseModel):
    """Hot cache, capado, con tenant+agente."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(default_factory=new_id)
    tenant_id: str
    agent_id: str
    content: str = Field(min_length=1, max_length=10000)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=now_utc)

class EpisodicEvent(BaseModel):
    """Append-only event log del agente."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(default_factory=new_id)
    tenant_id: str
    agent_id: str
    event_type: str = Field(min_length=1, max_length=128)
    payload: Dict[str, Any] = Field(default_factory=dict)
    correlation_id: Optional[str] = None
    created_at: datetime = Field(default_factory=now_utc)

    @field_validator("event_type")
    @classmethod
    def _etype(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("event_type vacio")
        return v.strip()

class SemanticFact(BaseModel):
    """Hecho estable upsert por key."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(default_factory=new_id)
    tenant_id: str
    agent_id: str
    key: str = Field(min_length=1, max_length=256, description="ej. cliente.email, empresa.nombre")
    value: Any
    source_belief_id: Optional[str] = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)

    @field_validator("key")
    @classmethod
    def _key(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("SemanticFact.key vacia")
        return v.strip()

class ProceduralSkill(BaseModel):
    """SOP del agente, versionado, upsert por name."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(default_factory=new_id)
    tenant_id: str
    agent_id: str
    name: str = Field(min_length=1, max_length=128)
    description: str = Field(default="")
    steps: List[Dict[str, Any]] = Field(default_factory=list)
    version: int = Field(default=1, ge=1)
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)

    @field_validator("name")
    @classmethod
    def _name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("ProceduralSkill.name vacia")
        return v.strip()
