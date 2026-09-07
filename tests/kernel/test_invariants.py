from agentic_os.kernel.world.events import EventLog, Event
from agentic_os.kernel.world.replay import replay


def test_replay_deterministic():
    log = EventLog()
    log.append(
        Event(
            kind="entity_created",
            entity_id="1",
            tenant_id="tenant-a",
            payload={
                "kind": "marketing.lead",
                "name": "Ana",
                "email": "ana@test.com",
            },
        )
    )
    s1 = replay(log)
    s2 = replay(log)
    assert s1.version == s2.version
    assert isinstance(s1.entities["1"].name, str)