from __future__ import annotations
from pydantic import BaseModel, Field, ConfigDict
from typing import Any, Dict, Optional
from ..kernel.types.ids import new_id
class ExecutionResult(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str = Field(default_factory=new_id)
    action_id: str
    success: bool
    output: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None

