from __future__ import annotations
from pydantic import BaseModel, Field, ConfigDict
from typing import Any, Dict, List, Optional
from ..types.ids import new_id
from ..types.time import now_utc
from datetime import datetime
class Event(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str = Field(default_factory=new_id)
    kind: str
    entity_id: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    at: datetime = Field(default_factory=now_utc)
    actor_id: Optional[str] = None
class EventLog(BaseModel):
    events: List[Event] = Field(default_factory=list)
    def append(self, e: Event) -> None:
        self.events.append(e)
    def __len__(self): return len(self.events)
