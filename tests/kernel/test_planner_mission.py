"""C5a/b/d: planner, MissionMemory, E2E plan -> memoria reconstruible."""
from __future__ import annotations

import pytest

from agentic_os.cognition.agents.seed import build_catalog
from agentic_os.cognition.planning.intent import Intent
from agentic_os.kernel.world.mission_memory import EventRef, Fact, MissionMemory
from agentic_os.orchestration.planner import (
    InvalidPlanError,
    UnknownIntentError,
    build_task_plan,
)


# ------------------------------------------------------ C5a planner

def test_planner_web_research_1_nodo():
    cat = build_catalog()
    plan = build_task_plan(Intent(goal="x", kind="web_research_agent"), cat)
    assert len(plan.nodes) == 1
    assert plan.nodes[0].agent_id == "web_research_agent"
    assert plan.nodes[0].depends_on == []


def test_planner_lead_generation_deps():
    cat = build_catalog()
    plan = build_task_plan(Intent(goal="x", kind="lead_generation_agent"), cat)
    ids = {n.agent_id for n in plan.nodes}
    assert "lead_generation_agent" in ids


def test_planner_reply_to_user_vacio():
    cat = build_catalog()
    plan = build_task_plan(Intent(goal="hi", kind="reply_to_user"), cat)
    assert plan.nodes == []


def test_planner_kind_desconocido_falla():
    cat = build_catalog()
    with pytest.raises(UnknownIntentError):
        build_task_plan(Intent(goal="x", kind="no-existe"), cat)


def test_planner_kind_vacio_falla():
    cat = build_catalog()
    with pytest.raises(UnknownIntentError):
        build_task_plan(Intent(goal="x", kind=""), cat)


def test_plan_frozen():
    from pydantic import ValidationError
    cat = build_catalog()
    plan = build_task_plan(Intent(goal="x", kind="web_research_agent"), cat)
    with pytest.raises(ValidationError):
        plan.mission = "otro"


# -------------------------------------------------- C5b MissionMemory

def test_mission_memory_vacia():
    m = MissionMemory(plan_id="p1")
    assert m.context == {}
    assert m.facts == []
    assert m.history == []


def test_with_node_output_no_muta():
    m = MissionMemory(plan_id="p1")
    m2 = m.with_node_output("n1", {"x": 1})
    assert m.context == {}
    assert m2.context == {"n1": {"x": 1}}


def test_with_fact_requiere_source():
    from pydantic import ValidationError
    m = MissionMemory(plan_id="p1")
    m2 = m.with_fact("acme is client", "web.search", 0.9)
    assert len(m2.facts) == 1
    assert m2.facts[0].source == "web.search"
    with pytest.raises(ValidationError):
        Fact(statement="x", source="")


def test_with_event_append():
    m = MissionMemory(plan_id="p1")
    m2 = m.with_event("e1", "PipelineStarted", "t1").with_event("e2", "PipelineCompleted", "t1")
    assert len(m2.history) == 2


# -------------------------------------------------- C5d E2E stub

def test_e2e_plan_y_memoria_reconstruible():
    """Simula el ciclo: Intent -> plan -> ejecucion stub -> MissionMemory."""
    cat = build_catalog()
    intent = Intent(goal="investiga ACME", kind="web_research_agent")
    plan = build_task_plan(intent, cat)
    assert len(plan.nodes) == 1

    # Simular que el nodo se ejecuta y produce output
    mem = MissionMemory(plan_id=plan.id, tenant_id="t1")
    for node in plan.nodes:
        output = {"agent": node.agent_id, "result": "ok"}
        mem = mem.with_node_output(node.id, output)
        mem = mem.with_event(f"ev-{node.id}", "NodeCompleted", "t1")

    assert mem.context[plan.nodes[0].id]["agent"] == "web_research_agent"
    assert len(mem.history) == len(plan.nodes)


def test_e2e_multi_agente_con_handoff():
    cat = build_catalog()
    intent = Intent(goal="consigue leads", kind="lead_generation_agent")
    plan = build_task_plan(intent, cat)
    mem = MissionMemory(plan_id=plan.id, tenant_id="t1")
    # Simular ejecucion de todos los nodos
    for node in plan.nodes:
        mem = mem.with_node_output(node.id, {"result": "ok"})
    assert len(mem.context) == len(plan.nodes)

