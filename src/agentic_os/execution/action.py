from __future__ import annotations
from pydantic import BaseModel, Field, ConfigDict
from typing import Any, Dict, Optional
from ..kernel.types.ids import new_id
from datetime import datetime
from ..kernel.types.time import now_utc
class Action(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str = Field(default_factory=new_id)
    capability: str
    actor_id: str
    resource_id: Optional[str] = None
    params: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=now_utc)

