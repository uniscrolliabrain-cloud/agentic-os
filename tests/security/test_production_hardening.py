from __future__ import annotations

from fastapi.testclient import TestClient

from agentic_os.execution.executor import Executor
from agentic_os.execution.tools import ToolRegistry
from agentic_os.execution.tools.gmail_tool import GmailSendTool
from agentic_os.infrastructure.persistence.jsonl import JsonlEventLog
from agentic_os.kernel.policy.engine import PolicyEngine
from agentic_os.kernel.world.events import Event


def test_event_requires_tenant():

    try:
        Event(
            kind="Test",
            entity_id="x",
            tenant_id="",
        )
    except Exception:
        return

    raise AssertionError(
        "Event sin tenant debería fallar"
    )


def test_executor_denies_unknown_tenant(
    tmp_path,
):

    log = JsonlEventLog(
        tmp_path / "events"
    )

    registry = ToolRegistry()

    registry.register(
        GmailSendTool()
    )

    executor = Executor(
        registry=registry,
        policy_engine=PolicyEngine(),
        event_log=log,
    )

    result = executor.execute(
        "gmail_send",
        {
            "to": "test@example.com",
            "subject": "test",
            "body": "test",
        },
        tenant_id="does-not-exist",
    )

    assert result["success"] is False


def test_correlation_id_is_preserved(
    tmp_path,
    monkeypatch,
):

    monkeypatch.setenv(
        "DEV_ALLOW_ALL",
        "true",
    )

    log = JsonlEventLog(
        tmp_path / "events"
    )

    registry = ToolRegistry()

    registry.register(
        GmailSendTool()
    )

    executor = Executor(
        registry=registry,
        policy_engine=PolicyEngine(),
        event_log=log,
    )

    correlation_id = "corr-test-001"
    command_id = "cmd-test-001"

    executor.execute(
        "gmail_send",
        {
            "to": "a@example.com",
            "subject": "hello",
            "body": "test",
        },
        tenant_id="test",
        correlation_id=correlation_id,
        command_id=command_id,
    )

    events = log.list_for_tenant(
        "test"
    )

    assert events

    assert all(
        event.correlation_id
        == correlation_id
        for event in events
    )

    assert all(
        event.command_id
        == command_id
        for event in events
    )