from __future__ import annotations

import inspect

import pytest

from agentic_os.execution.executor import Executor
from agentic_os.execution.tools import ToolRegistry, build_default_registry
from agentic_os.infrastructure.persistence.memory import (
    MemoryEventLog,
)
from agentic_os.kernel.policy.engine import PolicyEngine
from agentic_os.orchestration.orchestrator import Orchestrator
from agentic_os.orchestration.pipelines.runner import (
    PipelineRunner,
    PipelineStepError,
)
from agentic_os.orchestration import orchestrator as orchestrator_mod


class FakeTool:

    def __init__(
        self,
        name: str,
    ):
        self.name = name
        self.calls = 0

    def run(
        self,
        params,
    ):
        self.calls += 1
        return {
            "ok": True
        }


def test_pipeline_always_uses_executor():

    log = MemoryEventLog()

    registry = ToolRegistry()

    tool = FakeTool("fake_action")
    registry.register(tool)

    executor = Executor(
        registry=registry,
        policy_engine=PolicyEngine(),
        event_log=log,
    )

    runner = PipelineRunner(
        executor=executor
    )

    # Con default-deny (tenant desconocido) la ejecución NUNCA llega a la
    # FakeTool: el PipelineRunner lanza PipelineStepError con el motivo del
    # policy deny y la tool queda en cero llamadas.
    with pytest.raises(PipelineStepError):
        runner.tool(
            "fake_action",
            {},
            "unknown-tenant",
            "corr-1",
        )

    assert tool.calls == 0


def test_orchestrator_does_not_execute_tools_directly():
    source = inspect.getsource(orchestrator_mod)
    assert "_PipelineExecutorHost" not in source
    assert "tool.run(" not in source
    assert "connector.execute(" not in source
    assert "Executor(" not in source


def test_handle_pipeline_requires_injected_executor():
    orch = Orchestrator(log=MemoryEventLog(), llm=None)
    with pytest.raises(TypeError):
        orch.handle_pipeline("inbox_watcher", "t1")


def test_handle_pipeline_rejects_none_executor():
    orch = Orchestrator(log=MemoryEventLog(), llm=None)
    with pytest.raises(TypeError):
        orch.handle_pipeline(
            "inbox_watcher",
            "t1",
            executor=None,
        )


def test_handle_pipeline_rejects_mismatched_registry():
    log = MemoryEventLog()
    executor = Executor(
        registry=ToolRegistry(),
        policy_engine=PolicyEngine(),
        event_log=log,
    )
    orch = Orchestrator(log=log, llm=None)
    with pytest.raises(ValueError):
        orch.handle_pipeline(
            "inbox_watcher",
            "t1",
            executor=executor,
            registry=ToolRegistry(),
        )


def test_handle_pipeline_runner_receives_executor_and_execution_goes_through_it(
    monkeypatch,
):
    monkeypatch.setenv("DEV_ALLOW_ALL", "true")

    log = MemoryEventLog()
    registry = build_default_registry()
    executor = Executor(
        registry=registry,
        event_log=log,
    )
    original_execute = executor.execute
    execute_calls = []

    def tracking_execute(*args, **kwargs):
        execute_calls.append((args, kwargs))
        return original_execute(*args, **kwargs)

    executor.execute = tracking_execute

    captured = {}
    real_runner = PipelineRunner

    class TrackingRunner(PipelineRunner):
        def __init__(self, executor, llm=None):
            captured["executor"] = executor
            super().__init__(executor=executor, llm=llm)

    monkeypatch.setattr(
        "agentic_os.orchestration.pipelines.runner.PipelineRunner",
        TrackingRunner,
    )

    orch = Orchestrator(log=log, llm=None)
    result = orch.handle_pipeline(
        "inbox_watcher",
        "t2",
        executor=executor,
        registry=executor.registry,
    )

    assert captured["executor"] is executor
    assert execute_calls, "la ejecución no pasó por Executor.execute"
    assert result["status"] == "OK"