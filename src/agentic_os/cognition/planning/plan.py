from __future__ import annotations
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Any, List, Optional
from ...kernel.types.ids import new_id
class PlanStep(BaseModel):
    model_config = ConfigDict(frozen=True)
    capability: str
    resource_kind: Optional[str] = None
    params: dict[str, Any] = Field(default_factory=dict)

    @field_validator("capability")
    @classmethod
    def _capability_no_vacia(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("PlanStep.capability es obligatoria")
        return v

    @field_validator("params")
    @classmethod
    def _params_objeto(cls, value: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise ValueError("params must be an object")
        for key in value:
            if not isinstance(key, str):
                raise ValueError("params debe tener claves str")
        return value
class Plan(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str = Field(default_factory=new_id)
    intent_id: str
    steps: List[PlanStep] = Field(default_factory=list)

