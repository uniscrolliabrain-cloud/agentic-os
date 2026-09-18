"""Motor de composicion de agentes (spec 19)."""
from __future__ import annotations

from typing import Dict, List

from .catalog import Catalog
from .schemas import Handoff, TaskNode, TaskPlan


class CompositionError(ValueError):
    """Un handoff no resuelve a un agente del catalogo."""


def resolve_handoffs(plan: TaskPlan, catalog: Catalog) -> TaskPlan:
    """Expande un TaskPlan segun los handoffs declarados por cada agente.

    Para cada node del plan, si su agente declara handoffs_spec, se
    insertan nodos dependientes encadenados (payload_ref como input
    simulado). El resultado es un TaskPlan nuevo con DAG valido.

    Precondiciones:
    - Todo agent_id del plan existe en catalog.
    - Todo to_agent_id de los handoffs_spec existe en catalog.

    Postcondiciones:
    - El plan resultante pasa TaskPlan.__init__ (DAG sin ciclos).
    """
    if not plan.nodes:
        return plan

    # Validar que todos los agentes existen
    for node in plan.nodes:
        if catalog.agent(node.agent_id) is None:
            raise CompositionError(
                f"node {node.id!r}: agente {node.agent_id!r} no existe en el catalogo"
            )

    existing_ids = {n.id for n in plan.nodes}
    new_nodes: List[TaskNode] = list(plan.nodes)

    for node in plan.nodes:
        agent = catalog.agent(node.agent_id)
        if agent is None:
            continue
        for h in agent.handoffs_spec:
            target = catalog.agent(h.to_agent_id)
            if target is None:
                raise CompositionError(
                    f"handoff {h.from_agent_id} -> {h.to_agent_id}: agente destino no existe"
                )
            handoff_node_id = f"node-{node.id}-handoff-{h.to_agent_id}"
            if handoff_node_id in existing_ids:
                continue
            new_nodes.append(TaskNode(
                id=handoff_node_id,
                agent_id=h.to_agent_id,
                depends_on=[node.id],
                state="PENDING",
                input={"payload_ref": h.payload_ref} if h.payload_ref else {},
                output=None,
            ))
            existing_ids.add(handoff_node_id)

    if len(new_nodes) == len(plan.nodes):
        return plan

    return TaskPlan(
        id=plan.id,
        mission=plan.mission,
        nodes=new_nodes,
        owner_tenant_id=plan.owner_tenant_id,
    )


__all__ = ["CompositionError", "resolve_handoffs"]

