from ..kernel.world.replay import replay
from ..cognition.roles.library import LIBRARY

class Orchestrator:
def init(self, log):
self.log = log
self.current_role = LIBRARY["director"]
def tick(self):
state = replay(self.log)
return {"state": state, "role": self.current_role.name}
