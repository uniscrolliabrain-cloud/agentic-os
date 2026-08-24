from __future__ import annotations
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from ...kernel.types.ids import new_id
class PlanStep(BaseModel):
    model_config = ConfigDict(frozen=True)
    capability: str
    resource_kind: Optional[str] = None
    params: dict = Field(default_factory=dict)
class Plan(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str = Field(default_factory=new_id)
    intent_id: str
    steps: List[PlanStep] = Field(default_factory=list)
