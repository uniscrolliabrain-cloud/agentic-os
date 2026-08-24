from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, EmailStr


class SendEmailParams(BaseModel):
    """Pydantic model for sending email via Gmail."""
    model_config = ConfigDict(frozen=True)

    to: str = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email text body")
    cc: Optional[List[str]] = Field(default=None, description="Optional CC email recipients")


class CreateCalendarEventParams(BaseModel):
    """Pydantic model for creating a calendar event."""
    model_config = ConfigDict(frozen=True)

    title: str = Field(..., description="Title/Summary of the event")
    start_time: datetime = Field(..., description="Start timestamp of the event (ISO 8601)")
    end_time: datetime = Field(..., description="End timestamp of the event (ISO 8601)")
    attendees: List[str] = Field(default_factory=list, description="List of attendee email addresses")
    description: Optional[str] = Field(default=None, description="Detailed description or agenda")


class ReadFileParams(BaseModel):
    """Pydantic model for reading a file from Google Drive."""
    model_config = ConfigDict(frozen=True)

    file_id: str = Field(..., description="Google Drive file ID")
    mime_type: Optional[str] = Field(default="text/plain", description="MIME type for download")


class WorkspaceActionRequest(BaseModel):
    """Pydantic model for dispatching a workspace tool action."""
    model_config = ConfigDict(frozen=True)

    tool_name: str = Field(..., description="Name of the workspace tool to execute")
    capability: str = Field(..., description="Required capability for policy check")
    params: Dict[str, Any] = Field(default_factory=dict, description="Tool specific parameters")
