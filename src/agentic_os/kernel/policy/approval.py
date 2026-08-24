from __future__ import annotations
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from ..types.time import now_utc
from ..types.ids import new_id
class ApprovalRequest(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str = Field(default_factory=new_id)
    actor_id: str
    capability: str
    resource_id: Optional[str] = None
    reason: str = ""
    created_at: datetime = Field(default_factory=now_utc)
    status: str = "pending"
