from __future__ import annotations

from agentic_os.infrastructure.persistence.jsonl import (
    JsonlEventLog,
)
from agentic_os.kernel.world.events import Event


def test_jsonl_preserves_correlation_and_command(
    tmp_path,
):

    log = JsonlEventLog(
        tmp_path / "events"
    )

    event = Event(
        kind="ActionStarted",
        entity_id="gmail_send",
        tenant_id="tenant-a",
        correlation_id="corr-123",
        command_id="cmd-123",
        actor_id="executor",
    )

    log.append(event)

    events = log.list_for_tenant(
        "tenant-a"
    )

    assert len(events) == 1

    assert (
        events[0].correlation_id
        == "corr-123"
    )

    assert (
        events[0].command_id
        == "cmd-123"
    )