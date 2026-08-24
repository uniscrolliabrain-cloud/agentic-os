from __future__ import annotations
from pydantic import BaseModel, Field, ConfigDict
from ...kernel.types.ids import new_id
class Intent(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str = Field(default_factory=new_id)
    goal: str
    rationale: str = ""
