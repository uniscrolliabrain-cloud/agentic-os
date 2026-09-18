"""Planner determinista (spec 11). Construye TaskPlan a partir de Intent."""
from __future__ import annotations

from typing import Dict, List

from ..cognition.agents.catalog import Catalog
from ..cognition.agents.schemas import TaskNode, TaskPlan
from ..cognition.planning.intent import Intent
from ..kernel.types.ids import new_id


class UnknownIntentError(ValueError):
    """El Intent no resuelve a un agente del catalogo."""


class InvalidPlanError(ValueError):
    """El plan resultante no es un DAG valido."""


def build_task_plan(intent: Intent, catalog: Catalog) -> TaskPlan:
    """Construye un TaskPlan determinista a partir de un Intent.

    Precondiciones:
    - intent.kind resuelve a un agente del catalogo.

    Postcondiciones:
    - TaskPlan.nodes es un DAG valido.
    - TaskPlan.id es unico.

    El LLM nunca llama a esta funcion: la llama el orquestador.
    """
    if intent is None:
        raise UnknownIntentError("intent no puede ser None")

    # 1. Resolver intent.kind a un agente
    kind = (intent.kind or "").strip()
    if not kind:
        raise UnknownIntentError("intent.kind vacio")

    agent = catalog.agent(kind)
    if agent is None:
        # Fallback: reply_to_user es un pseudo-agente implicito
        if kind == "reply_to_user":
            return TaskPlan(
                id=f"plan-{new_id()}",
                mission=intent.goal or "reply to user",
                nodes=[],
                owner_tenant_id=None,
            )
        raise UnknownIntentError(
            f"kind {kind!r} no resuelve a ningun agente del catalogo"
        )

    # 2. Construir nodos: dependencias primero, luego el agente raiz
    nodes: List[TaskNode] = []
    node_by_agent: Dict[str, str] = {}

    def _add(agent_id: str, deps: List[str]) -> str:
        if agent_id in node_by_agent:
            return node_by_agent[agent_id]
        node_id = f"node-{agent_id}"
        nodes.append(TaskNode(
            id=node_id,
            agent_id=agent_id,
            depends_on=list(deps),
            state="PENDING",
            input={},
            output=None,
        ))
        node_by_agent[agent_id] = node_id
        return node_id

    # Dependencias (recursivo): cada dep del agente se crea primero
    def _resolve(agent_id: str, seen: set) -> str:
        if agent_id in seen:
            raise InvalidPlanError(f"ciclo detectado en dependencies: {agent_id}")
        a = catalog.agent(agent_id)
        if a is None:
            raise InvalidPlanError(f"agente {agent_id!r} no existe")
        dep_node_ids: List[str] = []
        for dep_id in a.dependencies:
            dep_node_ids.append(_resolve(dep_id, seen | {agent_id}))
        return _add(agent_id, dep_node_ids)

    _resolve(agent.id, set())

    plan = TaskPlan(
        id=f"plan-{new_id()}",
        mission=intent.goal or kind,
        nodes=nodes,
        owner_tenant_id=None,
    )
    return plan


__all__ = ["UnknownIntentError", "InvalidPlanError", "build_task_plan"]

