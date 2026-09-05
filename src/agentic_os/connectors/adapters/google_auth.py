"""Autenticación OAuth2 para adapters Google (Gmail, Drive, Calendar)."""
from __future__ import annotations

import logging
import threading
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from ...kernel.types.time import now_utc
from ...infrastructure.config.settings import settings as _settings
from ..auth.oauth_manager import OAuthManager
from ..core.errors import AuthenticationError

logger = logging.getLogger(__name__)


class MissingCredentials(Exception):
    """No hay credenciales Google configuradas en Settings/.env."""


class GoogleAuth:
    """Obtiene y cachea el access token de Google OAuth2.

    Construye la configuración OAuth desde ``Settings`` (variables GOOGLE_*)
    y refresca el token vía ``OAuthManager.refresh()``. Thread-safe.
    """

    def __init__(self, settings: Any = _settings):
        self._settings = settings
        self._lock = threading.Lock()
        self._access_token: Optional[str] = None
        self._expires_at: Optional[datetime] = None

    def _oauth_config(self) -> Dict[str, Any]:
        s = self._settings
        client_id = s.google_client_id
        refresh_token = s.google_refresh_token
        if not (client_id and refresh_token):
            raise MissingCredentials(
                "Faltan GOOGLE_CLIENT_ID / GOOGLE_REFRESH_TOKEN en Settings/.env"
            )
        return {
            "client_id": client_id,
            "client_secret": s.google_client_secret or "",
            "token_url": "https://oauth2.googleapis.com/token",
        }

    def access_token(self) -> str:
        """Devuelve un access token válido, refrescando si es necesario (thread-safe)."""
        with self._lock:
            if self._access_token and self._expires_at:
                now = now_utc()
                if now < self._expires_at - timedelta(seconds=60):
                    return self._access_token
            return self._refresh_locked()

    def _refresh_locked(self) -> str:
        cfg = self._oauth_config()
        refresh_token = self._settings.google_refresh_token
        result = OAuthManager.refresh(cfg, refresh_token)
        if not result or "access_token" not in result:
            raise AuthenticationError(
                "No se pudo refrescar el token de Google (respuesta inválida)",
                provider="google",
            )
        self._access_token = result["access_token"]
        expires_in = result.get("expires_in", 3600)
        self._expires_at = now_utc() + timedelta(seconds=expires_in)
        logger.info("Token de Google refrescado (expires_in=%ss)", expires_in)
        return self._access_token
