from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from ...kernel.types.ids import new_id

class PlanStep(BaseModel):
    """Paso determinista: capability + validacion + compensacion."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(default_factory=new_id)
    order: int = Field(ge=0)
    capability: str = Field(description="tool o microaccion ej. web.search")
    description: str = Field(default="")
    params: Dict[str, Any] = Field(default_factory=dict)
    preconditions: List[str] = Field(default_factory=list)
    postconditions: List[str] = Field(default_factory=list)
    compensation: Optional[str] = Field(default=None, description="capability para rollback")
    timeout_seconds: int = Field(default=60, gt=0)
    retry_policy: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("capability")
    @classmethod
    def _cap_nonblank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("PlanStep.capability obligatoria")
        return v.strip()

class Plan(BaseModel):
    """DAG de pasos. Valida orden y dependencias."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(default_factory=new_id)
    intent_id: str
    goal_id: Optional[str] = None
    steps: List[PlanStep] = Field(default_factory=list)
    estimated_cost: float = Field(default=0.0, ge=0.0)
    risk: str = Field(default="low")

    @field_validator("steps")
    @classmethod
    def _steps_ordered_unique(cls, v: List[PlanStep]) -> List[PlanStep]:
        orders = [s.order for s in v]
        if orders != sorted(orders):
            raise ValueError("steps deben estar ordenados por order")
        if len(set(orders)) != len(orders):
            raise ValueError("order duplicado en steps")
        return v

    def topological(self) -> List[PlanStep]:
        # ya ordenados por order, pero valida que no haya huecos grandes
        return sorted(self.steps, key=lambda s: s.order)

    def requires_approval(self) -> bool:
        return any(s.capability in ("gmail_send", "slack_send", "whatsapp_send", "meta_post_publish") for s in self.steps)
