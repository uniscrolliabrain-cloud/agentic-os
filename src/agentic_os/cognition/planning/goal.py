from __future__ import annotations
from pydantic import BaseModel, Field, ConfigDict
from ...kernel.types.ids import new_id
class Goal(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str = Field(default_factory=new_id)
    description: str
    priority: int = 0
