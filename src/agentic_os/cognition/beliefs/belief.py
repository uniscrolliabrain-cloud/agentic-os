from __future__ import annotations
from pydantic import BaseModel, Field, ConfigDict
from typing import Any, Dict, Optional
from datetime import datetime
from ...kernel.types.time import now_utc
from ...kernel.types.ids import new_id
class Belief(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str = Field(default_factory=new_id)
    kind: str
    content: Dict[str, Any]
    confidence: float = 1.0
    source_observation_id: Optional[str] = None
    created_at: datetime = Field(default_factory=now_utc)
