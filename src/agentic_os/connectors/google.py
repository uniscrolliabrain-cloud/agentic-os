"""Google Connectors â€” Conecta Gmail, Drive y Calendar reales vÃ­a adapters.

Lee credenciales de Settings/.env (GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET,
GOOGLE_REFRESH_TOKEN) y expone conectores funcionales registrados en el
CapabilityRegistry.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional

from .adapters.google_auth import GoogleAuth, MissingCredentials
from .adapters.google_gmail import GoogleGmailAdapter
from .adapters.google_drive import GoogleDriveAdapter
from .adapters.google_calendar import GoogleCalendarAdapter
from .core.base import Connector
from .core.models import Command, CommandResult

logger = logging.getLogger(__name__)


class GoogleConnector(Connector):
    """Connector real de Google que delega en adapters especÃ­ficos.

    Soporta capabilities:
    - email.message.read / email.message.send (Gmail)
    - file.read / file.create (Drive)
    - calendar.event.create / calendar.event.read (Calendar)
    """

    def __init__(self, provider: str = "google"):
        self.connector_id = "google"
        self.provider = provider
        self.capabilities = [
            "email.message.read", "email.message.send",
            "file.read", "file.create",
            "calendar.event.create", "calendar.event.read",
        ]
        self.auth_type = "oauth2"
        self.connected = False
        self._auth: Optional[GoogleAuth] = None
        self._gmail: Optional[GoogleGmailAdapter] = None
        self._drive: Optional[GoogleDriveAdapter] = None
        self._calendar: Optional[GoogleCalendarAdapter] = None
        self._try_connect()

    def _try_connect(self) -> None:
        """Intenta conectar leyendo credenciales de Settings/.env."""
        try:
            self._auth = GoogleAuth()
            _ = self._auth._oauth_config()
            self.connected = True
            logger.info("Google connector conectado (credenciales OK)")
        except MissingCredentials as e:
            self.connected = False
            logger.warning("Google connector sin conectar: %s", e)
        except Exception as e:
            self.connected = False
            logger.warning("Google connector error: %s", e)

    def _ensure_connected(self) -> None:
        if not self.connected:
            raise Exception("Google connector no conectado (faltan credenciales)")

    async def execute(self, command: Command) -> CommandResult:
        """Ejecuta el comando de forma asÃ­ncrona (delegaciÃ³n en hilos)."""
        self._ensure_connected()
        loop = asyncio.get_event_loop()
        try:
            capability = command.capability
            params = command.params
            if capability == "email.message.read":
                return await loop.run_in_executor(None, self._read_email, params)
            elif capability == "email.message.send":
                return await loop.run_in_executor(None, self._send_email, params)
            elif capability == "file.read":
                return await loop.run_in_executor(None, self._read_file, params)
            elif capability == "file.create":
                return await loop.run_in_executor(None, self._create_file, params)
            elif capability == "calendar.event.create":
                return await loop.run_in_executor(None, self._create_event, params)
            elif capability == "calendar.event.read":
                return await loop.run_in_executor(None, self._read_events, params)
            else:
                return CommandResult(
                    ok=False,
                    error=f"Capability '{capability}' no soportada",
                    error_type="UNSUPPORTED_CAPABILITY",
                    execution_id=command.execution_id,
                    connector_id=self.connector_id,
                    capability=command.capability,
                )
        except Exception as e:
            return CommandResult(
                ok=False,
                error=str(e),
                error_type="EXECUTION_ERROR",
                execution_id=command.execution_id,
                connector_id=self.connector_id,
                capability=command.capability,
            )

    def _read_email(self, params: Dict[str, Any]) -> CommandResult:
        gmail = self._gmail or GoogleGmailAdapter(self._auth)
        self._gmail = gmail
        message_id = params.get("message_id")
        if message_id:
            msg = gmail.get_message(message_id)
        else:
            msg = gmail.list_messages(max_results=params.get("max_results", 10))
        return CommandResult(
            ok=True, output=msg,
            connector_id=self.connector_id, provider=self.provider,
            capability="email.message.read",
        )

    def _send_email(self, params: Dict[str, Any]) -> CommandResult:
        gmail = self._gmail or GoogleGmailAdapter(self._auth)
        self._gmail = gmail
        result = gmail.send_message(
            to=params["to"], subject=params.get("subject", ""),
            body=params.get("body", ""), from_addr=params.get("from"),
        )
        return CommandResult(
            ok=True, output=result,
            connector_id=self.connector_id, provider=self.provider,
            capability="email.message.send",
        )

    def _read_file(self, params: Dict[str, Any]) -> CommandResult:
        drive = self._drive or GoogleDriveAdapter(self._auth)
        self._drive = drive
        file_id = params.get("file_id")
        if file_id:
            result = drive.read_file(file_id)
        else:
            result = drive.list_files(folder_id=params.get("folder_id"))
        return CommandResult(
            ok=True, output=result,
            connector_id=self.connector_id, provider=self.provider,
            capability="file.read",
        )

    def _create_file(self, params: Dict[str, Any]) -> CommandResult:
        drive = self._drive or GoogleDriveAdapter(self._auth)
        self._drive = drive
        result = drive.create_file(
            name=params.get("name", "untitled.txt"),
            content=params.get("content", ""),
            mime_type=params.get("mime_type", "text/plain"),
            folder_id=params.get("folder_id"),
        )
        return CommandResult(
            ok=True, output=result,
            connector_id=self.connector_id, provider=self.provider,
            capability="file.create",
        )

    def _create_event(self, params: Dict[str, Any]) -> CommandResult:
        cal = self._calendar or GoogleCalendarAdapter(self._auth)
        self._calendar = cal
        result = cal.create_event(
            title=params.get("title", "Sin tÃ­tulo"),
            start=params["start"], end=params["end"],
            attendees=params.get("attendees"),
        )
        return CommandResult(
            ok=True, output=result,
            connector_id=self.connector_id, provider=self.provider,
            capability="calendar.event.create",
        )

    def _read_events(self, params: Dict[str, Any]) -> CommandResult:
        cal = self._calendar or GoogleCalendarAdapter(self._auth)
        self._calendar = cal
        result = cal.list_events(
            max_results=params.get("max_results", 10),
            time_min=params.get("time_min"),
        )
        return CommandResult(
            ok=True, output=result,
            connector_id=self.connector_id, provider=self.provider,
            capability="calendar.event.read",
        )


def register_google_connector(registry: Any):
    """Registra el Google connector en el CapabilityRegistry."""
    try:
        conn = GoogleConnector()
        registry.register(conn)
        logger.info("Google connector registrado (connected=%s)", conn.connected)
        return conn
    except Exception as e:  # noqa: BLE001
        logger.warning("No se pudo registrar el Google connector: %s", e)
        return None

