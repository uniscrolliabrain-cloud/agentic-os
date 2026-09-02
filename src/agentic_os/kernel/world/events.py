from __future__ import annotations

import threading
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, field_validator

from ..types.ids import new_id
from ..types.time import now_utc


class Event(BaseModel):
    """
    Evento inmutable del sistema.

    Invariantes:
    - Todo evento pertenece a un tenant.
    - Todo evento tiene identidad propia.
    - correlation_id permite reconstruir una ejecución completa.
    - command_id identifica la misión/comando lógico que originó la ejecución.
    """

    model_config = ConfigDict(frozen=True)

    id: str = Field(default_factory=new_id)
    kind: str
    entity_id: str

    payload: Dict[str, Any] = Field(default_factory=dict)

    at: datetime = Field(default_factory=now_utc)

    actor_id: Optional[str] = None

    tenant_id: str = Field(
        description="Tenant al que pertenece el evento."
    )

    correlation_id: Optional[str] = Field(
        default=None,
        description=(
            "ID de correlación de la ejecución. "
            "Permite reconstruir Mission -> Pipeline -> Action -> Tool."
        ),
    )

    command_id: Optional[str] = Field(
        default=None,
        description=(
            "ID lógico de la misión/comando que originó el evento."
        ),
    )

    @field_validator("tenant_id")
    @classmethod
    def _tenant_id_not_empty(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("tenant_id obligatorio (invariante multi-tenant)")
        return value

    def __str__(self) -> str:
        return (
            f"Event[{self.tenant_id}:"
            f"{self.kind}:"
            f"{self.entity_id}]"
        )


class EventLog(BaseModel):
    """
    EventLog en memoria.

    Se utiliza principalmente en tests.
    Producción utiliza un EventLogRepository persistente.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    events: List[Event] = Field(default_factory=list)

    _lock: threading.RLock = PrivateAttr(
        default_factory=threading.RLock
    )

    def append(self, event: Event) -> None:
        if not event.tenant_id:
            raise ValueError(
                "Event sin tenant_id rechazado: "
                "viola la invariante multi-tenant."
            )

        with self._lock:
            self.events.append(event)

    def for_tenant(self, tenant_id: str) -> List[Event]:
        with self._lock:
            return [
                event
                for event in self.events
                if event.tenant_id == tenant_id
            ]

    def list_for_tenant(self, tenant_id: str) -> List[Event]:
        return self.for_tenant(tenant_id)

    def all_events(self) -> List[Event]:
        with self._lock:
            return list(self.events)

    def list_all(self) -> List[Event]:
        return self.all_events()

    def __len__(self) -> int:
        with self._lock:
            return len(self.events)
