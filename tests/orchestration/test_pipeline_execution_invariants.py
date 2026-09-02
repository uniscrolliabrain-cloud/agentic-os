from __future__ import annotations

import pytest

from agentic_os.execution.executor import Executor
from agentic_os.execution.tools import ToolRegistry
from agentic_os.infrastructure.persistence.memory import (
    MemoryEventLog,
)
from agentic_os.kernel.policy.engine import PolicyEngine
from agentic_os.orchestration.pipelines.runner import (
    PipelineRunner,
    PipelineStepError,
)


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