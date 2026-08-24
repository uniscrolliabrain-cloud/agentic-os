from __future__ import annotations
from pydantic import BaseModel, ConfigDict, Field
from typing import List
class Capability(BaseModel):
    model_config = ConfigDict(frozen=True)
    name: str
    description: str = ""
    requires_tools: List[str] = Field(default_factory=list)
