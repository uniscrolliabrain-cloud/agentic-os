"""C7a: MicroAction* events, retry, timeout, output_schema (specs 12, 16, 17)."""
from __future__ import annotations

import pytest

from agentic_os.execution.executor import Executor
from agentic_os.execution.tools.base import Tool
from agentic_os.execution.tools.registry import ToolRegistry
from agentic_os.infrastructure.persistence.memory import MemoryEventLog
from agentic_os.kernel.policy.engine import PolicyEngine
from agentic_os.orchestration.pipelines.runner import (
    PipelineRunner,
    PipelineStepError,
)


class FlakyTool(Tool):
    """Falla 2 veces y a la 3 funciona."""
    name = "flaky_tool"
    attempts = 0

    def run(self, params):
        FlakyTool.attempts += 1
        if FlakyTool.attempts < 3:
            raise RuntimeError(f"fallo transitorio {FlakyTool.attempts}")
        return {"ok": True, "attempts": FlakyTool.attempts}


class SlowTool(Tool):
    name = "slow_tool"

    def run(self, params):
        import time
        time.sleep(2.0)
        return {"done": True}


class BadOutputTool(Tool):
    name = "bad_output_tool"

    def run(self, params):
        return {"count": "no-es-int"}


class GoodOutputTool(Tool):
    name = "good_output_tool"

    def run(self, params):
        return {"count": 42, "name": "acme"}


def _runner(tools, monkeypatch):
    monkeypatch.setenv("DEV_ALLOW_ALL", "true")
    reg = ToolRegistry()
    for t in tools:
        reg.register(t)
    log = MemoryEventLog()
    ex = Executor(registry=reg, policy_engine=PolicyEngine(), event_log=log)
    return PipelineRunner(executor=ex, llm=None), log


def test_micro_action_started_completed(monkeypatch):
    runner, log = _runner([GoodOutputTool()], monkeypatch)
    out = runner.tool("good_output_tool", {}, "t1")
    assert out["count"] == 42
    kinds = [e.kind for e in log.list_for_tenant("t1")]
    assert "MicroActionStarted" in kinds
    assert "MicroActionCompleted" in kinds


def test_micro_action_failed_en_eventlog(monkeypatch):
    class AlwaysFail(Tool):
        name = "always_fail"
        def run(self, params):
            raise RuntimeError("boom")

    runner, log = _runner([AlwaysFail()], monkeypatch)
    with pytest.raises(PipelineStepError):
        runner.tool("always_fail", {}, "t2")
    kinds = [e.kind for e in log.list_for_tenant("t2")]
    assert "MicroActionFailed" in kinds


def test_retry_policy(monkeypatch):
    FlakyTool.attempts = 0
    runner, log = _runner([FlakyTool()], monkeypatch)
    out = runner.tool(
        "flaky_tool", {}, "t3",
        retry_policy={"max_retries": 3, "backoff": 1.0},
    )
    assert out["ok"] is True
    assert out["attempts"] == 3


def test_timeout(monkeypatch):
    runner, log = _runner([SlowTool()], monkeypatch)
    with pytest.raises(PipelineStepError, match="timeout"):
        runner.tool("slow_tool", {}, "t4", timeout_seconds=1)


def test_output_schema_ok(monkeypatch):
    runner, log = _runner([GoodOutputTool()], monkeypatch)
    out = runner.tool(
        "good_output_tool", {}, "t5",
        output_schema={
            "type": "object",
            "required": ["count", "name"],
            "properties": {"count": {"type": "integer"}, "name": {"type": "string"}},
        },
    )
    assert out["count"] == 42


def test_output_schema_falla_por_tipo(monkeypatch):
    runner, log = _runner([BadOutputTool()], monkeypatch)
    with pytest.raises(PipelineStepError, match="output_schema"):
        runner.tool(
            "bad_output_tool", {}, "t6",
            output_schema={
                "type": "object",
                "properties": {"count": {"type": "integer"}},
            },
        )


def test_output_schema_falla_por_falta_required(monkeypatch):
    runner, log = _runner([GoodOutputTool()], monkeypatch)
    with pytest.raises(PipelineStepError, match="faltan claves"):
        runner.tool(
            "good_output_tool", {}, "t7",
            output_schema={"type": "object", "required": ["inexistente"]},
        )

