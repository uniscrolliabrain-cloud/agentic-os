from __future__ import annotations
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

class EpisodicMemory(BaseModel):
    """Append-only wrapper. La implementacion real es CognitionStore.episodic_*"""

    model_config = ConfigDict(frozen=False, extra="forbid")

    events: List[dict] = Field(default_factory=list)

    def append(self, event_type: str, payload: dict, correlation_id: Optional[str] = None) -> None:
        self.events.append({
            "event_type": event_type,
            "payload": payload,
            "correlation_id": correlation_id,
            "at": datetime.utcnow().isoformat(),
        })

    def replay(self, since: Optional[datetime] = None, event_type: Optional[str] = None) -> List[dict]:
        ev = self.events
        if event_type:
            ev = [e for e in ev if e.get("event_type") == event_type]
        if since:
            ev = [e for e in ev if e.get("at") and e.get("at") >= since.isoformat()]
        return ev
