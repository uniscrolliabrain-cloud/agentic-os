from __future__ import annotations
from pydantic import BaseModel, Field, ConfigDict
from typing import Any, Dict
from datetime import datetime
from ...kernel.types.time import now_utc
from ...kernel.types.ids import new_id
class Observation(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str = Field(default_factory=new_id)
    source: str
    data: Dict[str, Any]
    at: datetime = Field(default_factory=now_utc)
