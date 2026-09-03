from __future__ import annotations

from typing import Any, Dict

from ...kernel.types.time import now_utc
from .base import Tool, ToolValidationError


class CalendarCreateEventTool(Tool):
    """Tool determinista de Calendar: crea un evento en el calendario del tenant."""

    name = "calendar_create_event"

    def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        title = params.get("title", "")
        start = params.get("start", "")
        end = params.get("end", "")
        attendees = params.get("attendees", [])

        if not title or not start:
            raise ToolValidationError("faltan campos: title y start son obligatorios")

        return {
            "status": "SIMULATED",
            "real_execution": False,
            "title": title,
            "start": start,
            "end": end or start,
            "attendees": attendees,
            "event_id": f"cal-{abs(hash(title + start))}",
            "created_at": now_utc().isoformat(),
        }


class CalendarListEventsTool(Tool):
    """Tool determinista de Calendar: lista eventos del calendario."""

    name = "calendar_list_events"

    def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        max_results = int(params.get("max_results", 5))

        return {
            "status": "SIMULATED",
            "real_execution": False,
            "max_results": max_results,
            "events": [
                {
                    "id": "evt-001",
                    "title": "Reunión con cliente",
                    "start": "2026-08-26T10:00:00",
                    "end": "2026-08-26T11:00:00",
                },
                {
                    "id": "evt-002",
                    "title": "Seguimiento proyecto",
                    "start": "2026-08-27T15:00:00",
                    "end": "2026-08-27T16:00:00",
                },
            ],
        }