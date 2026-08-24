from __future__ import annotations
from .events import EventLog
from .state import WorldState
from .applier import apply
def replay(log: EventLog) -> WorldState:
    state = WorldState()
    for e in log.events:
        state = apply(state, e)
    return state
