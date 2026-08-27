"""StubConnector: provider concreto base.

Crea la infraestructura de un provider SIN conectar a la API real.
`connected=False` por defecto; las credenciales reales se inyectan vía
.env/secretos. El código nunca contiene valores reales.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from ..core.base import Connector
from ..core.errors import ConnectorUnavailable
from ..core.config import ConnectorConfig


class StubConnector(Connector):
    """Connector concreto base: infraestructura lista, API no conectada."""

    def __init__(
        self,
        connector_id: str,
        provider: str,
        capabilities: list = None,
        auth_type: str = "none",
        oauth: dict | None = None,
        config: Optional[Dict[str, Any]] = None,
        credentials: Optional[Dict[str, Any]] = None,
        connected: bool = False,
    ):
        self.connector_id = connector_id
        self.provider = provider
        self.capabilities = capabilities or []
        self.auth_type = auth_type
        self._oauth_config = oauth or {}
        self._config = config or {}
        self._credentials = credentials or {}
        self.connected = connected and bool(credentials)
        self._resolved_credentials: Optional[Dict[str, Any]] = None

    async def health_check(self):
        if not self.connected:
            from ..core.models import HealthStatusModel
            return HealthStatusModel(
                status="AUTH_REQUIRED",
                provider=self.provider,
                detail=f"Connector '{self.connector_id}' creado pero sin conectar (sin credenciales).",
            )
        return await super().health_check()

    async def execute(self, command):
        # dry-run nunca toca la API: siempre devuelve preview, conectado o no
        if command.dry_run:
            return self._stub_preview(command)
        if not self.connected:
            return self._not_configured(command)
        raise ConnectorUnavailable(
            f"Adapter '{self.provider}' sin conectar: no hay credenciales/configuración.",
            capability=command.capability,
        )
