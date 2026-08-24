from __future__ import annotations
from ..kernel.world.events import EventLog
from ..kernel.world.replay import replay
class Orchestrator:
    def __init__(self, log: EventLog):
        self.log = log
    def tick(self):
        state = replay(self.log)
        return state
