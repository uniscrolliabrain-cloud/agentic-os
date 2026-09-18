"""C7c: TaskScheduler - orden topologico, pausa approval, resume."""
from __future__ import annotations

import pytest

from agentic_os.cognition.agents.schemas import TaskNode, TaskPlan
from agentic_os.infrastructure.persistence.memory import MemoryEventLog
from agentic_os.orchestration.task_scheduler import (
    PlanPausedForApproval,
    SchedulerError,
    TaskScheduler,
)


def _plan_chain():
    return TaskPlan(
        id="p1", mission="m",
        nodes=[
            TaskNode(id="n1", agent_id="a1"),
            TaskNode(id="n2", agent_id="a2", depends_on=["n1"]),
            TaskNode(id="n3", agent_id="a3", depends_on=["n2"]),
        ],
    )


def test_scheduler_orden_topologico():
    order = []
    def runner(node, ctx):
        order.append(node.id)
        return {"state": "COMPLETED", "output": {"ok": True}}
    s = TaskScheduler(_plan_chain(), runner)
    res = s.run()
    assert order == ["n1", "n2", "n3"]
    assert res["status"] == "COMPLETED"


def test_scheduler_pausa_por_approval():
    def runner(node, ctx):
        if node.id == "n2":
            return {"state": "NEEDS_APPROVAL"}
        return {"state": "COMPLETED", "output": {}}
    log = MemoryEventLog()
    s = TaskScheduler(_plan_chain(), runner, event_log=log, tenant_id="t1")
    with pytest.raises(PlanPausedForApproval) as exc:
        s.run()
    assert exc.value.node_id == "n2"
    kinds = [e.kind for e in log.list_for_tenant("t1")]
    assert "PlanPausedForApproval" in kinds


def test_scheduler_resume_aprobado():
    state = {"approved": False}
    def runner(node, ctx):
        if node.id == "n2" and not state["approved"]:
            return {"state": "NEEDS_APPROVAL"}
        return {"state": "COMPLETED", "output": {"ok": True}}
    s = TaskScheduler(_plan_chain(), runner)
    with pytest.raises(PlanPausedForApproval):
        s.run()
    state["approved"] = True
    res = s.resume("n2", approved=True)
    assert res["status"] == "COMPLETED"


def test_scheduler_resume_rechazado():
    def runner(node, ctx):
        if node.id == "n2":
            return {"state": "NEEDS_APPROVAL"}
        return {"state": "COMPLETED"}
    s = TaskScheduler(_plan_chain(), runner)
    with pytest.raises(PlanPausedForApproval):
        s.run()
    res = s.resume("n2", approved=False)
    assert res["states"]["n2"] == "CANCELLED"


def test_scheduler_failed_bloquea_dependientes():
    def runner(node, ctx):
        if node.id == "n1":
            raise RuntimeError("boom")
        return {"state": "COMPLETED"}
    s = TaskScheduler(_plan_chain(), runner)
    res = s.run()
    assert res["states"]["n1"] == "FAILED"
    assert res["states"]["n2"] == "BLOCKED"
    assert res["states"]["n3"] == "BLOCKED"


def test_scheduler_dep_huerfana_falla():
    plan = TaskPlan(
        id="p1", mission="m",
        nodes=[TaskNode(id="n1", agent_id="a1")],
    )
    broken = TaskNode(id="n2", agent_id="a2", depends_on=["inexistente"])
    plan_broken = plan.model_copy(update={"nodes": [broken]})
    s = TaskScheduler(plan_broken, lambda n, c: {})
    with pytest.raises(SchedulerError):
        s.run()


def test_scheduler_emite_eventos():
    log = MemoryEventLog()
    s = TaskScheduler(
        _plan_chain(),
        lambda n, c: {"state": "COMPLETED", "output": {}},
        event_log=log, tenant_id="t1",
    )
    s.run()
    kinds = [e.kind for e in log.list_for_tenant("t1")]
    assert "NodeDispatched" in kinds
    assert "NodeCompleted" in kinds

