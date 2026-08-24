from __future__ import annotations
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Literal
Effect = Literal["allow","deny","require_approval"]
class PolicyRule(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str
    description: str = ""
    capability: str
    resource_kind: Optional[str] = None
    effect: Effect = "allow"
    requires_roles: List[str] = Field(default_factory=list)
class Policy(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str
    name: str
    rules: List[PolicyRule] = Field(default_factory=list)
    version: int = 1
