"""C7b: TaskNode.state, Handoff, resolve_handoffs (specs 05, 19)."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from agentic_os.cognition.agents.catalog import Catalog
from agentic_os.cognition.agents.composition import (
    CompositionError,
    resolve_handoffs,
)
from agentic_os.cognition.agents.schemas import (
    Handoff,
    MiniAgentSchema,
    TaskNode,
    TaskPlan,
)


# ---------------------------------------------- TaskNode.state

def test_tasknode_state_default_pending():
    n = TaskNode(id="n1", agent_id="a1")
    assert n.state == "PENDING"


def test_tasknode_state_invalido_falla():
    with pytest.raises(ValidationError, match="TaskNode.state"):
        TaskNode(id="n1", agent_id="a1", state="VOLANDO")


def test_tasknode_state_runing_ok():
    n = TaskNode(id="n1", agent_id="a1", state="RUNNING")
    assert n.state == "RUNNING"


def test_tasknode_no_acepta_status():
    with pytest.raises(ValidationError):
        TaskNode(id="n1", agent_id="a1", status="pending")


# ---------------------------------------------- Handoff

def test_handoff_minimo():
    h = Handoff(from_agent_id="a", to_agent_id="b")
    assert h.from_agent_id == "a"
    assert h.payload_ref == ""


def test_handoff_sin_from_falla():
    with pytest.raises(ValidationError):
        Handoff(from_agent_id="", to_agent_id="b")


def test_handoff_sin_to_falla():
    with pytest.raises(ValidationError):
        Handoff(from_agent_id="a", to_agent_id="")


# ---------------------------------------------- resolve_handoffs

def _cat_with_handoff():
    cat = Catalog()
    cat.declare_tool("t1")
    cat.add_microaction.__self__ if False else None  # placeholder
    # Registrar dos agentes: A declara handoff hacia B
    from agentic_os.cognition.agents.schemas import MicroActionSchema
    cat.add_microaction(MicroActionSchema(
        id="ma.read", action_type="Read", entity_type="Document",
        taxonomy="DOCUMENTS", purpose="read", tool="t1",
    ))
    cat.add_agent(MiniAgentSchema(
        id="a", name="A", microactions=["ma.read"], tools=["t1"],
        handoffs_spec=[Handoff(from_agent_id="a", to_agent_id="b", payload_ref="out")],
    ))
    cat.add_agent(MiniAgentSchema(
        id="b", name="B", microactions=["ma.read"], tools=["t1"],
    ))
    return cat


def test_resolve_handoffs_sin_handoff_no_cambia():
    cat = _cat_with_handoff()
    plan = TaskPlan(
        id="p1", mission="m",
        nodes=[TaskNode(id="n-b", agent_id="b")],
    )
    out = resolve_handoffs(plan, cat)
    assert len(out.nodes) == 1


def test_resolve_handoffs_crea_nodo_dependiente():
    cat = _cat_with_handoff()
    plan = TaskPlan(
        id="p1", mission="m",
        nodes=[TaskNode(id="n-a", agent_id="a")],
    )
    out = resolve_handoffs(plan, cat)
    assert len(out.nodes) == 2
    handoff_node = [n for n in out.nodes if "handoff" in n.id][0]
    assert handoff_node.agent_id == "b"
    assert handoff_node.depends_on == ["n-a"]


def test_resolve_handoffs_agente_destino_inexistente():
    cat = Catalog()
    cat.declare_tool("t1")
    from agentic_os.cognition.agents.schemas import MicroActionSchema
    cat.add_microaction(MicroActionSchema(
        id="ma.read", action_type="Read", entity_type="Document",
        taxonomy="DOCUMENTS", purpose="read", tool="t1",
    ))
    # Agente con handoff a un agente que no existe
    cat.add_agent(MiniAgentSchema(
        id="b", name="B", microactions=["ma.read"], tools=["t1"],
    ))
    # Al construirlo el Catalog no valida handoffs_spec, pero resolve_handoffs si
    plan = TaskPlan(id="p1", mission="m", nodes=[TaskNode(id="n-b", agent_id="b")])
    # Parchear el agente para tener un handoff a inexistente
    agent_b = cat.agent("b")
    bad = agent_b.model_copy(update={
        "handoffs_spec": [Handoff(from_agent_id="b", to_agent_id="no-existe")],
    })
    cat._agents["b"] = bad
    with pytest.raises(CompositionError):
        resolve_handoffs(plan, cat)

