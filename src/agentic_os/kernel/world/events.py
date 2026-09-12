from __future__ import annotations

import threading
from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, field_validator, model_validator

from ..types import KernelModel
from ..ontology.domain_models import BaseDomainModel
from ..ontology.vocabulary import Vocabulary
from ..types.ids import new_id
from ..types.time import now_utc

T = TypeVar("T", bound=BaseDomainModel)

EVENT_VOCAB = Vocabulary(
    entities={
        "entity_created",
        "entity_updated",
        "entity_deleted",
        "relation_created",
        "relation_deleted",
        "IntentProposed",
        "BackgroundProcessingDone",
        "BackgroundProcessingFailed",
        "ScheduledPipelineStarted",
        "ScheduledPipelineFailed",
        "ScheduledPipelineFinished",
        "ActionStarted",
        "ToolCompleted",
        "ToolFailed",
        "ActionDenied",
        "sales.lead.created",
    }
)


class Event(KernelModel, Generic[T]):
    id: str = Field(default_factory=new_id)
    entity_id: str
    tenant_id: str = Field(description="Tenant al que pertenece el evento.")

    event_type: Optional[str] = None
    data: Optional[T] = None

    kind: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None

    at: datetime = Field(default_factory=now_utc)

    actor_id: Optional[str] = None

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
            "ID lógico de la misión/comando que originó la ejecución."
        ),
    )

    @field_validator("tenant_id")
    @classmethod
    def _tenant_id_not_empty(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("tenant_id obligatorio (invariante multi-tenant)")
        return value

    @model_validator(mode="after")
    def _validate_event_usage(self) -> "Event[T]":
        typed = self.event_type is not None
        legacy = self.kind is not None or self.payload is not None
        if typed and legacy:
            raise ValueError(
                "Usa event_type + data tipado o kind + payload legacy, no ambos"
            )
        if self.event_type is not None and self.event_type not in EVENT_VOCAB.entities:
            raise ValueError(
                f"event_type no registrado en el Vocabulary: {self.event_type!r}"
            )
        return self

    def __str__(self) -> str:
        kind = self.event_type or self.kind or ""
        return (
            f"Event[{self.tenant_id}:"
            f"{kind}:"
            f"{self.entity_id}]"
        )


class EventLog(BaseModel):
    """
    EventLog en memoria.

    Se utiliza principalmente en tests.
    Producción utiliza un EventLogRepository persistente.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    events: List[Event[Any]] = Field(default_factory=list)

    _lock: threading.RLock = PrivateAttr(
        default_factory=threading.RLock
    )

    def append(self, event: Event[Any]) -> None:
        if not event.tenant_id:
            raise ValueError(
                "Event sin tenant_id rechazado: "
                "viola la invariante multi-tenant."
            )

        with self._lock:
            self.events.append(event)

    def for_tenant(self, tenant_id: str) -> List[Event[Any]]:
        with self._lock:
            return [
                event
                for event in self.events
                if event.tenant_id == tenant_id
            ]

    def list_for_tenant(self, tenant_id: str) -> List[Event[Any]]:
        return self.for_tenant(tenant_id)

    def all_events(self) -> List[Event[Any]]:
        with self._lock:
            return list(self.events)

    def list_all(self) -> List[Event[Any]]:
        return self.all_events()

    def __len__(self) -> int:
        with self._lock:
            return len(self.events)




