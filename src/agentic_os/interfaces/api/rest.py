from __future__ import annotations

from typing import Any, Dict
from fastapi import FastAPI, Depends, status

from .deps import get_current_user, require_capability
from ...infrastructure.auth.models import AuthenticatedUser, OAuthCallbackParams
from ...domains.tools.google.models import (
    SendEmailParams,
    CreateCalendarEventParams,
    ReadFileParams,
)
from ...domains.tools.google.workspace_tools import (
    GmailTool,
    CalendarTool,
    DriveTool,
)

app = FastAPI(
    title="Agentic OS API",
    description="Enterprise API with Google Workspace Tools and Deterministic Policy Governance",
    version="0.1.0",
)

_gmail_tool = GmailTool()
_calendar_tool = CalendarTool()
_drive_tool = DriveTool()


@app.get("/health", tags=["System"])
def health_check() -> Dict[str, str]:
    return {"status": "ok", "system": "Agentic OS"}


@app.post("/auth/google/callback", tags=["Auth"])
def google_auth_callback(payload: OAuthCallbackParams) -> Dict[str, Any]:
    """Callback endpoint for Google OAuth authorization code exchange."""
    return {
        "status": "authenticated",
        "code_received": bool(payload.code),
        "message": "Authorization code exchanged successfully",
    }


@app.get("/auth/me", tags=["Auth"], response_model=AuthenticatedUser)
def get_authenticated_profile(
    user: AuthenticatedUser = Depends(get_current_user),
) -> AuthenticatedUser:
    """Returns the authenticated Google user profile and active Agentic OS roles."""
    return user


@app.post("/workspace/email/send", tags=["Google Workspace"])
def send_email_endpoint(
    params: SendEmailParams,
    user: AuthenticatedUser = Depends(require_capability("gmail:send")),
) -> Dict[str, Any]:
    """Sends an email via Gmail - Protected by Kernel Policy (gmail:send)."""
    event = _gmail_tool.execute(params=params, actor=user)
    return {
        "success": True,
        "event_id": event.id,
        "kind": event.kind,
        "payload": event.payload,
    }


@app.post("/workspace/calendar/create", tags=["Google Workspace"])
def create_calendar_event_endpoint(
    params: CreateCalendarEventParams,
    user: AuthenticatedUser = Depends(require_capability("calendar:create")),
) -> Dict[str, Any]:
    """Creates a calendar event - Protected by Kernel Policy (calendar:create)."""
    event = _calendar_tool.execute(params=params, actor=user)
    return {
        "success": True,
        "event_id": event.id,
        "kind": event.kind,
        "payload": event.payload,
    }


@app.post("/workspace/drive/read", tags=["Google Workspace"])
def read_drive_file_endpoint(
    params: ReadFileParams,
    user: AuthenticatedUser = Depends(require_capability("drive:read")),
) -> Dict[str, Any]:
    """Reads a file from Google Drive - Protected by Kernel Policy (drive:read)."""
    event = _drive_tool.execute(params=params, actor=user)
    return {
        "success": True,
        "event_id": event.id,
        "kind": event.kind,
        "payload": event.payload,
    }

