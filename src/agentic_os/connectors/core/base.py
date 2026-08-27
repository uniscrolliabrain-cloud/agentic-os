"""Interfaz común de todos los connectors y adaptadores de provider.

Un Connector solo puede ejecutar capabilities registradas. Nunca permite
ejecución arbitraria. Los providers se crean SIN conectar a las APIs destino:
`execute` devuelve CONNECTOR_NOT_CONFIGURED hasta que haya credenciales reales.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from .errors import ConnectorUnavailable
from .models import Command, CommandResult, CredentialStatus, HealthStatusModel


class Connector(ABC):
    """Contrato común de todo connector."""

    connector_id: str = "base"
    provider: str = "base"
    version: str = "0.0.0"
    capabilities: List[str] = []
    auth_type: str = "none"          # api_key | bearer | basic | oauth2 | custom_header
    connected: bool = False          # False = creado pero sin conectar (sin credenciales)

    # ------------------------------------------------------------- soporte --
    def supports(self, capability: str) -> bool:
        return capability in self.capabilities

    def list_capabilities(self) -> List[str]:
        return list(self.capabilities)

    # ------------------------------------------------------------- salud ----
    async def health_check(self) -> HealthStatusModel:
        """Devuelve AUTH_REQUIRED/UNAVAILABLE mientras no haya credenciales reales."""
        if not self.connected:
            return HealthStatusModel(
                status="AUTH_REQUIRED",
                provider=self.provider,
                detail=f"Connector '{self.connector_id}' creado pero sin conectar (sin credenciales).",
            )
        return HealthStatusModel(status="HEALTHY", provider=self.provider)

    async def validate_credentials(self) -> CredentialStatus:
        if not self.connected:
            return CredentialStatus(status="missing", provider=self.provider, detail="No configurado aún")
        return CredentialStatus(status="valid", provider=self.provider)

    # ------------------------------------------------------------ ejecución --
    @abstractmethod
    async def execute(self, command: Command) -> CommandResult:
        """Ejecuta un Command. Mientras el connector esté sin conectar, devuelve
        un CommandResult con error CONNECTOR_NOT_CONFIGURED (stub controlado)."""

    # ------------------------------------------------------------ helper ----
    def _not_configured(self, command: Command) -> CommandResult:
        return CommandResult(
            ok=False,
            error="Connector creado pero no conectado a la API destino (falta credenciales/configuración).",
            error_type="CONNECTOR_NOT_CONFIGURED",
            execution_id=command.execution_id,
            connector_id=self.connector_id,
            provider=self.provider,
            capability=command.capability,
        )

    def _stub_preview(self, command: Command) -> CommandResult:
        """Respuesta de dry-run para un connector sin conexión: describe lo que
        PASARÍA sin ejecutarlo."""
        return CommandResult(
            ok=True,
            dry_run=True,
            preview={
                "connector": self.connector_id,
                "provider": self.provider,
                "capability": command.capability,
                "operation": f"{self.provider}::{command.capability}",
                "payload_summary": {k: v for k, v in command.params.items()},
                "risk": "READ_ONLY",
                "note": "dry-run: no se ejecutó efecto externo (connector sin conectar)",
            },
            execution_id=command.execution_id,
            connector_id=self.connector_id,
            provider=self.provider,
            capability=command.capability,
        )


class ProviderAdapter(ABC):
    """Adaptador que traduce capability canónica → llamada específica del provider.

    Se implementa por provider cuando se conecta. Mientras no haya credenciales,
    los adaptadores quedan registrados pero no invocan la API real."""

    provider: str = "base"
    api_version: str = "1.0"
    connector_version: str = "0.0.0"
    capability_version: str = "1.0"

    def __init__(self, credentials: Optional[Dict[str, Any]] = None, config: Optional[Dict[str, Any]] = None):
        self.credentials = credentials or {}
        self.config = config or {}

    @abstractmethod
    async def call(self, capability: str, params: Dict[str, Any]) -> Any:
        """Traduce y ejecuta la capability contra el provider. Lanzará
        ConnectorUnavailable mientras no esté conectado."""
        raise ConnectorUnavailable(
            f"Adapter '{self.provider}' sin conectar: no hay credenciales/configuración."
        )