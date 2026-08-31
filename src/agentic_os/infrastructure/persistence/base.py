from __future__ import annotations
from typing import Protocol, List
from...kernel.world.events import Event

class EventLogRepository(Protocol):
    def append(self, event: Event) -> None:...
    def list_for_tenant(self, tenant_id: str) -> List[Event]:...
    def list_all(self) -> List[Event]:...

    def all_events(self) -> List[Event]:
        """FASE 3.1 (bugfix de tipo): lectura total común de la interfaz.

        El Orquestador y replay() usan este método de interfaz, nunca
        atributos concretos como `log.events` (que solo existe en el
        EventLog in-memory de tests).
        """
        ...

