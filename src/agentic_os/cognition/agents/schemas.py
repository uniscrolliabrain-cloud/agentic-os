"""Contratos Pydantic del sistema de agentes (spec 07_PYDANTIC_CONTRACTS.md).

Reglas invariables:
- Todos los modelos son frozen=True, extra="forbid".
- Los ids son strings no vacíos y estables (son referencias del catálogo).
- Un agente/pipeline/microacción que no valide NO se registra (fail-closed).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ...kernel.ontology.action_types import ACTION_TYPES, is_forbidden_pair
from ...kernel.ontology.taxonomy import is_valid_taxonomy


from ...kernel.ontology.action_types import ACTION_TYPES, is_forbidden_pair
from ...kernel.ontology.taxonomy import is_valid_taxonomy

class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class MicroActionSchema(_Frozen):
    """Operacion atomica con contrato cerrado (docs/spec/08)."""

    id: str
    action_type: str
    entity_type: str
    taxonomy: str
    purpose: str
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    preconditions: List[str] = Field(default_factory=list)
    tool: str
    output_schema: Dict[str, Any] = Field(default_factory=dict)
    validation: List[str] = Field(default_factory=list)
    error_states: List[str] = Field(default_factory=list)
    handoff: List[str] = Field(default_factory=list)
    timeout_seconds: int = 60
    retry_policy: Dict[str, Any] = Field(default_factory=dict)
    stub: bool = False

    @field_validator("id", "action_type", "entity_type", "taxonomy", "purpose", "tool")
    @classmethod
    def _nonblank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("campo obligatorio en blanco")
        return v

    @field_validator("taxonomy")
    @classmethod
    def _taxonomy_valida(cls, v: str) -> str:
        if not is_valid_taxonomy(v):
            raise ValueError(f"taxonomy invalida: {v!r}")
        return v

    @field_validator("action_type")
    @classmethod
    def _action_type_valido(cls, v: str) -> str:
        if v not in ACTION_TYPES:
            raise ValueError(f"action_type invalido: {v!r}")
        return v

    @field_validator("entity_type")
    @classmethod
    def _pair_no_prohibido(cls, v: str, info) -> str:
        action = info.data.get("action_type")
        if action and is_forbidden_pair(action, v):
            raise ValueError(f"par prohibido por defecto: ({action}, {v})")
        return v

    @field_validator("timeout_seconds")
    @classmethod
    def _positive_timeout(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("timeout_seconds debe ser > 0")
        return v

class PipelineStep(_Frozen):
    order: int
    microaction_id: str
    param_override: Dict[str, Any] = Field(default_factory=dict)
    if_else: Optional[Dict[str, Any]] = None

    @field_validator("order")
    @classmethod
    def _order_nonnegative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("order no puede ser negativo")
        return v

    @field_validator("microaction_id")
    @classmethod
    def _ma_nonblank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("microaction_id obligatorio")
        return v


class PipelineSchema(_Frozen):
    id: str
    name: str
    purpose: str
    steps: List[PipelineStep] = Field(default_factory=list)
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    output_schema: Dict[str, Any] = Field(default_factory=dict)
    error_recovery: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("steps")
    @classmethod
    def _steps_ordered(cls, v: List[PipelineStep]) -> List[PipelineStep]:
        orders = [s.order for s in v]
        if orders != sorted(orders):
            raise ValueError("steps deben estar ordenados por 'order'")
        if len(set(orders)) != len(orders):
            raise ValueError("steps con 'order' duplicado")
        return v


class MiniAgentSchema(_Frozen):
    id: str
    name: str
    version: str = "1.0"
    ontology: Dict[str, Any] = Field(default_factory=dict)
    purpose: str = ""
    triggers: List[str] = Field(default_factory=list)
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    input_validation: List[str] = Field(default_factory=list)
    preconditions: List[str] = Field(default_factory=list)
    microactions: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    decision_rules: List[str] = Field(default_factory=list)
    sop: str = ""
    postconditions: List[str] = Field(default_factory=list)
    output_schema: Dict[str, Any] = Field(default_factory=dict)
    output_validation: List[str] = Field(default_factory=list)
    error_types: List[str] = Field(default_factory=list)
    retry_policy: Dict[str, Any] = Field(default_factory=dict)
    timeout_policy: Dict[str, Any] = Field(default_factory=dict)
    permission_policy: Dict[str, Any] = Field(default_factory=dict)
    human_approval_policy: Dict[str, Any] = Field(default_factory=dict)
    state_transitions: Dict[str, Any] = Field(default_factory=dict)
    handoffs: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    observability: List[str] = Field(default_factory=list)
    test_cases: List[str] = Field(default_factory=list)

    @field_validator("id", "name")
    @classmethod
    def _nonblank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("id/name obligatorio")
        return v


class TaskNode(_Frozen):
    id: str
    agent_id: str
    depends_on: List[str] = Field(default_factory=list)
    status: str = "pending"
    input: Dict[str, Any] = Field(default_factory=dict)
    output: Optional[Dict[str, Any]] = None


class TaskPlan(_Frozen):
    id: str
    mission: str
    nodes: List[TaskNode] = Field(default_factory=list)
    owner_tenant_id: Optional[str] = None

    @field_validator("nodes")
    @classmethod
    def _no_cycle_and_valid_deps(cls, nodes: List[TaskNode]) -> List[TaskNode]:
        ids = {n.id for n in nodes}
        if len(ids) != len(nodes):
            raise ValueError("TaskPlan: node.id duplicado")
        for n in nodes:
            for dep in n.depends_on:
                if dep not in ids:
                    raise ValueError(f"node {n.id!r} depende de {dep!r} inexistente")
        incoming: Dict[str, int] = {n.id: 0 for n in nodes}
        adj: Dict[str, List[str]] = {n.id: [] for n in nodes}
        for n in nodes:
            for dep in n.depends_on:
                adj[dep].append(n.id)
                incoming[n.id] += 1
        frontier = [i for i, c in incoming.items() if c == 0]
        seen = 0
        while frontier:
            cur = frontier.pop()
            seen += 1
            for nxt in adj[cur]:
                incoming[nxt] -= 1
                if incoming[nxt] == 0:
                    frontier.append(nxt)
        if seen != len(nodes):
            raise ValueError("TaskPlan: dependencias cíclicas")
        return nodes
