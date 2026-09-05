"""Adapter real de Google Gmail API v1."""
from __future__ import annotations

import base64
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional

import httpx

from ..core.errors import AuthenticationError, NotFoundError, ProviderError
from .google_auth import GoogleAuth

BASE_URL = "https://gmail.googleapis.com/gmail/v1"


class GoogleGmailAdapter:
    """Cliente síncrono para Google Gmail API v1."""

    def __init__(self, auth: Optional[GoogleAuth] = None):
        self._auth = auth or GoogleAuth()
        self._client = httpx.Client(timeout=30.0, http2=False)

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self._auth.access_token()}"}

    def _request(self, method: str, path: str, **kwargs: Any) -> Dict[str, Any]:
        url = f"{BASE_URL}{path}"
        resp = self._client.request(method, url, headers=self._headers(), **kwargs)
        if resp.status_code == 404:
            raise NotFoundError(f"Recurso Gmail no encontrado: {path}", provider="google")
        if resp.status_code in (401, 403):
            raise AuthenticationError(
                f"Error autenticación Google Gmail ({resp.status_code})",
                provider="google",
                code=resp.status_code,
            )
        if resp.status_code >= 400:
            raise ProviderError(
                f"Error Google Gmail ({resp.status_code}): {resp.text[:200]}",
                provider="google",
                code=resp.status_code,
            )
        return resp.json()

    def list_messages(self, max_results: int = 10, query: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lista mensajes del usuario autenticado."""
        params = {"maxResults": min(max_results, 100)}
        if query:
            params["q"] = query
        data = self._request("GET", "/users/me/messages", params=params)
        return [
            {
                "id": m.get("id", ""),
                "thread_id": m.get("threadId", ""),
                "snippet": m.get("snippet", ""),
            }
            for m in data.get("messages", [])
        ]

    def get_message(self, message_id: str) -> Dict[str, Any]:
        """Obtiene el contenido completo de un mensaje."""
        data = self._request("GET", f"/users/me/messages/{message_id}", params={"format": "full"})
        headers = {h["name"]: h["value"] for h in data.get("payload", {}).get("headers", [])}
        body = ""
        payload = data.get("payload", {})
        if "parts" in payload:
            for part in payload["parts"]:
                if part.get("mimeType") == "text/plain":
                    body_data = part.get("body", {}).get("data", "")
                    body = base64.urlsafe_b64decode(body_data).decode("utf-8", errors="replace")
                    break
        elif payload.get("body", {}).get("data"):
            body_data = payload["body"]["data"]
            body = base64.urlsafe_b64decode(body_data).decode("utf-8", errors="replace")
        return {
            "id": data.get("id", ""),
            "thread_id": data.get("threadId", ""),
            "from": headers.get("From", ""),
            "to": headers.get("To", ""),
            "subject": headers.get("Subject", ""),
            "date": headers.get("Date", ""),
            "body": body,
            "snippet": data.get("snippet", ""),
        }

    def send_message(self, to: str, subject: str, body: str, from_addr: Optional[str] = None) -> Dict[str, Any]:
        """Envía un email vía Gmail API."""
        msg = MIMEText(body)
        msg["to"] = to
        msg["subject"] = subject
        if from_addr:
            msg["from"] = from_addr
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        result = self._request("POST", "/users/me/messages/send", json={"raw": raw})
        return {
            "id": result.get("id", ""),
            "thread_id": result.get("threadId", ""),
            "label_ids": result.get("labelIds", []),
        }

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "GoogleGmailAdapter":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()