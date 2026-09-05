"""Adapter real de Google Calendar API v3."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

from ..core.errors import AuthenticationError, NotFoundError, ProviderError
from .google_auth import GoogleAuth
from ...kernel.types.time import now_utc

BASE_URL = "https://www.googleapis.com/calendar/v3"


class GoogleCalendarAdapter:
    """Cliente síncrono para Google Calendar API v3."""

    def __init__(self, auth: Optional[GoogleAuth] = None):
        self._auth = auth or GoogleAuth()
        self._client = httpx.Client(timeout=30.0, http2=False)

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self._auth.access_token()}"}

    def _request(self, method: str, path: str, **kwargs: Any) -> Dict[str, Any]:
        url = f"{BASE_URL}{path}"
        resp = self._client.request(method, url, headers=self._headers(), **kwargs)
        if resp.status_code == 404:
            raise NotFoundError(f"Evento/calendario no encontrado: {path}", provider="google")
        if resp.status_code in (401, 403):
            raise AuthenticationError(
                f"Error autenticación Google Calendar ({resp.status_code})",
                provider="google",
                code=resp.status_code,
            )
        if resp.status_code >= 400:
            raise ProviderError(
                f"Error Google Calendar ({resp.status_code}): {resp.text[:200]}",
                provider="google",
                code=resp.status_code,
            )
        return resp.json()

    def create_event(self, title: str, start: str, end: str, attendees: Optional[List[str]] = None) -> Dict[str, Any]:
        """Crea un evento en el calendario primario."""
        body: Dict[str, Any] = {"summary": title, "start": {"dateTime": start}, "end": {"dateTime": end}}
        if attendees:
            body["attendees"] = [{"email": e} for e in attendees if "@" in e]
        result = self._request("POST", "/calendars/primary/events", json=body)
        return {
            "id": result.get("id", ""),
            "summary": result.get("summary", title),
            "start": result.get("start", {}).get("dateTime", start),
            "end": result.get("end", {}).get("dateTime", end),
            "link": result.get("htmlLink", ""),
        }

    def list_events(self, max_results: int = 10, time_min: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lista eventos próximos del calendario primario."""
        if time_min is None:
            time_min = now_utc().isoformat()
        params = {"timeMin": time_min, "maxResults": min(max_results, 100), "singleEvents": "true", "orderBy": "startTime"}
        data = self._request("GET", "/calendars/primary/events", params=params)
        return [
            {
                "id": e.get("id", ""),
                "title": e.get("summary", ""),
                "start": (e.get("start") or {}).get("dateTime", ""),
                "end": (e.get("end") or {}).get("dateTime", ""),
            }
            for e in data.get("items", [])
        ]

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "GoogleCalendarAdapter":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()
