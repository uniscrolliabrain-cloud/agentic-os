from __future__ import annotations

from uuid import uuid4

from ...kernel.types.time import now_utc
from ..core.models import Command


class TelemetryEvent:
    """Evento de observabilidad para una ejecución de connector."""

    def __init__(
        self,
        event_type: str,
        command: Command,
        connector_id: str,
        provider: str,
        workspace_id: str | None = None,
        correlation_id: str | None = None,
        payload: dict | None = None,
    ):
        self.event_id = str(uuid4())
        self.event_type = event_type
        self.timestamp = now_utc()
        self.workspace_id = workspace_id
        self.correlation_id = correlation_id or command.correlation_id
        self.command_id = command.execution_id
        self.connector_id = connector_id
        self.provider = provider
        self.capability = command.capability
        self.payload = payload or {}


class EventRecorder:
    """Registra eventos de ejecución. Nunca logs con secrets."""

    def __init__(self, sink: list | None = None):
        self._events: list = sink if sink is not None else []

    def emit(self, event_type: str, command: Command, connector_id: str,
             provider: str, **payload) -> TelemetryEvent:
        event = TelemetryEvent(
            event_type=event_type,
            command=command,
            connector_id=connector_id,
            provider=provider,
            payload=payload,
        )
        self._events.append(event)
        return event

    def events(self) -> list:
        return list(self._events)
