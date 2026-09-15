from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from ...kernel.types.ids import new_id
from ...kernel.types.time import now_utc

class GoalStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    ACHIEVED = "achieved"
    FAILED = "failed"
    ABANDONED = "abandoned"

class Goal(BaseModel):
    """Objetivo SMART auditado. No es un string suelto."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(default_factory=new_id)
    description: str = Field(min_length=3, max_length=2000)
    priority: int = Field(default=0, ge=0, le=100)
    status: GoalStatus = GoalStatus.PENDING
    parent_goal_id: Optional[str] = None
    criteria: List[str] = Field(default_factory=list, description="criterios de exito verificables")
    constraints: List[str] = Field(default_factory=list)
    owner_tenant_id: str = Field(default="system")
    owner_agent_id: Optional[str] = None
    created_at: datetime = Field(default_factory=now_utc)
    due_at: Optional[datetime] = None

    @field_validator("description")
    @classmethod
    def _desc_nonblank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Goal.description vacia")
        return v.strip()

class GoalStack(BaseModel):
    """Pila de objetivos con orden por prioridad. Evita goal-thrashing."""

    model_config = ConfigDict(frozen=False, extra="forbid")

    goals: List[Goal] = Field(default_factory=list)

    def push(self, goal: Goal) -> None:
        self.goals.append(goal)
        self.goals.sort(key=lambda g: (-g.priority, g.created_at))

    def pop_next(self) -> Optional[Goal]:
        for g in self.goals:
            if g.status in (GoalStatus.PENDING, GoalStatus.ACTIVE):
                return g
        return None

    def mark(self, goal_id: str, status: GoalStatus) -> None:
        for i, g in enumerate(self.goals):
            if g.id == goal_id:
                self.goals[i] = g.model_copy(update={"status": status})
                return
        raise KeyError(f"goal {goal_id!r} no encontrado")
