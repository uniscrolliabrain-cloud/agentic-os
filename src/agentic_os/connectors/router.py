"""ConnectorRouter: selecciona el connector adecuado para una capability canónica.

Algoritmo (caps 6/51-56 del manual):
  1. existe capability
  2. workspace tiene provider configurado
  3. existen credenciales
  4. credenciales válidas
  5. connector sano
  6. connector soporta la capability exacta
  7. policy de permisos
  8. rate-limit disponible
  9. seleccionar
  10. ejecutar

Nunca deja al LLM elegir provider arbitrariamente.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .core.base import Connector
from .core.errors import (
    AuthenticationError,
    ConnectorError,
    ConnectorUnavailable,
    NormalizedError,
    UnsupportedOperationError,
)
from .core.models import Command, CommandResult, HealthStatus
from .registry import CapabilityRegistry


class ConnectorRouter:
    def __init__(self, registry: Optional[CapabilityRegistry] = None) -> None:
        self.registry = registry or CapabilityRegistry()

    def candidate_ids(self, capability: str) -> List[str]:
        return [c.connector_id for c in self.registry.resolve(capability)]

    async def select(self, capability: str) -> Connector:
        """Elige el connector para una capability según el algoritmo determinista."""
        if not self.registry.has_capability(capability):
            raise UnsupportedOperationError(
                f"La capability '{capability}' no está registrada en ningún connector",
                capability=capability,
            )
        candidates = self.registry.resolve(capability)
        for conn in candidates:
            # 5. salud: se evita conector no sano salvo instrucción explícita
            health = await conn.health_check()
            if health.status in (HealthStatus.DISABLED, HealthStatus.UNAVAILABLE):
                continue
            # 4. credenciales
            cred = await conn.validate_credentials()
            if conn.connected and cred.status in ("missing", "invalid", "revoked"):
                continue
            if conn.supports(capability):
                return conn
        raise ConnectorUnavailable(
            f"Ningún connector disponible para '{capability}' (o creado sin conectar).",
            capability=capability,
        )

    async def route(self, command: Command) -> CommandResult:
        """Selecciona y ejecuta el command. Si el conector no está conectado,
        devuelve el stub controlado (CONNECTOR_NOT_CONFIGURED)."""
        try:
            conn = await self.select(command.capability)
        except ConnectorError as e:
            return self._error_result(command, e)
        try:
            return await conn.execute(command)
        except ConnectorError as e:
            return self._error_result(command, e)
        except Exception as e:  # noqa: BLE001
            return self._error_result(command, ConnectorError(str(e)))

    @staticmethod
    def _error_result(command: Command, e: ConnectorError) -> CommandResult:
        return CommandResult(
            ok=False,
            error=str(e) or e.message,
            error_type=getattr(e, "error_type", NormalizedError.UNKNOWN_ERROR),
            execution_id=command.execution_id,
            capability=command.capability,
            provider=getattr(e, "provider", None),
        )