from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Dict, Any
class WorldState(BaseModel):
    entities: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    relations: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    version: int = 0
