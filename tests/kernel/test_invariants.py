from agentic_os.kernel.world.events import EventLog, Event
from agentic_os.kernel.world.replay import replay
def test_replay_deterministic():
    log = EventLog()
    log.append(Event(kind="entity_created", entity_id="1", payload={"kind":"actor"}))
    s1 = replay(log)
    s2 = replay(log)
    assert s1.version == s2.version
