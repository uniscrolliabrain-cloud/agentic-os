from __future__ import annotations

from abc import abstractmethod
from typing import Any, Dict, Generic, Optional, Type, TypeVar
from pydantic import BaseModel

from ....execution.tools.base import Tool
from ....kernel.world.events import Event
from ....infrastructure.auth.models import AuthenticatedUser
from .models import (
    SendEmailParams,
    CreateCalendarEventParams,
    ReadFileParams,
)

P = TypeVar("P", bound=BaseModel)


class BaseWorkspaceTool(Tool, Generic[P]):
    """Abstract base class for Google Workspace tools producing deterministic Events."""

    name: str
    capability: str
    param_schema: Type[P]

    @abstractmethod
    def execute(self, params: P, actor: Optional[AuthenticatedUser] = None) -> Event:
        """Executes tool logic and returns a kernel Event."""
        pass

    def run(self, params: Dict[str, Any] | BaseModel) -> Dict[str, Any]:
        """Implements Tool.run for Executor integration."""
        if isinstance(params, self.param_schema):
            validated_params = params
        elif isinstance(params, dict):
            validated_params = self.param_schema.model_validate(params)
        else:
            validated_params = self.param_schema.model_validate(params.model_dump())

        event = self.execute(validated_params)
        return {
            "event_id": event.id,
            "kind": event.kind,
            "entity_id": event.entity_id,
            "payload": event.payload,
        }


class GmailTool(BaseWorkspaceTool[SendEmailParams]):
    """Tool for sending emails via Gmail."""

    name = "gmail_send_email"
    capability = "gmail:send"
    param_schema = SendEmailParams

    def execute(self, params: SendEmailParams, actor: Optional[AuthenticatedUser] = None) -> Event:
        payload: Dict[str, Any] = {
            "to": params.to,
            "subject": params.subject,
            "body": params.body,
            "cc": params.cc or [],
            "status": "sent",
        }
        return Event(
            kind="email_sent",
            entity_id=params.to,
            payload=payload,
            actor_id=actor.id if actor else None,
        )


class CalendarTool(BaseWorkspaceTool[CreateCalendarEventParams]):
    """Tool for scheduling events via Google Calendar."""

    name = "calendar_create_event"
    capability = "calendar:create"
    param_schema = CreateCalendarEventParams

    def execute(
        self, params: CreateCalendarEventParams, actor: Optional[AuthenticatedUser] = None
    ) -> Event:
        payload: Dict[str, Any] = {
            "title": params.title,
            "start_time": params.start_time.isoformat(),
            "end_time": params.end_time.isoformat(),
            "attendees": params.attendees,
            "description": params.description or "",
            "status": "confirmed",
        }
        return Event(
            kind="calendar_event_created",
            entity_id=f"event_{params.title.replace(' ', '_').lower()}",
            payload=payload,
            actor_id=actor.id if actor else None,
        )


class DriveTool(BaseWorkspaceTool[ReadFileParams]):
    """Tool for reading documents from Google Drive."""

    name = "drive_read_file"
    capability = "drive:read"
    param_schema = ReadFileParams

    def execute(self, params: ReadFileParams, actor: Optional[AuthenticatedUser] = None) -> Event:
        payload: Dict[str, Any] = {
            "file_id": params.file_id,
            "mime_type": params.mime_type or "text/plain",
            "content": f"[Simulated Content for file {params.file_id}]",
            "status": "read",
        }
        return Event(
            kind="drive_file_read",
            entity_id=params.file_id,
            payload=payload,
            actor_id=actor.id if actor else None,
        )
