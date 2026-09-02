from __future__ import annotations

from threading import RLock
from typing import List

from ...kernel.world.events import Event
from .base import EventLogRepository


class InMemoryEventLog(EventLogRepository):
    """EventLog en memoria, thread-safe (uso en tests y fallback)."""

    def __init__(self) -> None:
        self._events: List[Event] = []
        self._lock = RLock()

    def append(self, event: Event) -> None:
        with self._lock:
            self._events.append(event)

    def list_for_tenant(self, tenant_id: str) -> List[Event]:
        with self._lock:
            return [e for e in self._events if e.tenant_id == tenant_id]

    def list_all(self) -> List[Event]:
        with self._lock:
            return list(self._events)


# Alias para compatibilidad: el nombre histórico aceptado por los tests.
MemoryEventLog = InMemoryEventLog