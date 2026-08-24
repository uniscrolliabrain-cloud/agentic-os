from __future__ import annotations
from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Any
from ..types.ids import new_id
from ..types.time import now_utc
from datetime import datetime
class Relation(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str = Field(default_factory=new_id)
    kind: str
    src_id: str
    dst_id: str
    attributes: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=now_utc)
