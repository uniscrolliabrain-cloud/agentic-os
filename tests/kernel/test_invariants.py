from __future__ import annotations

import pytest

from agentic_os.domains._examples import register_demo_entities
from agentic_os.kernel.world.events import Event, EventLog
from agentic_os.kernel.world.replay import replay


@pytest.fixture(autouse=True)
def _demo_entities():
    register_demo_entities()
    yield


def test_replay_deterministic():
    log = EventLog()
    log.append(Event(
        kind="entity_created", entity_id="1", tenant_id="tenant-a",
        payload={"kind": "marketing.lead", "name": "Ana", "email": "ana@test.com"},
    ))
    s1 = replay(log)
    s2 = replay(log)
    assert s1.version == s2.version
    assert isinstance(s1.entities["1"].name, str)