"""ConnectorFactory: instancia connectors a partir de configuración registrada.
Los agentes NUNCA instancian connectors directamente."""

from __future__ import annotations

from typing import Any, Dict, Optional

from .core.base import Connector
from .core.errors import ConnectorUnavailable


class ConnectorFactory:
    """Mantiene el mapa de fabricantes (provider -> clase Connector) y los instancia."""

    def __init__(self) -> None:
        self._builders: Dict[str, Any] = {}

    def register_builder(self, provider: str, builder) -> None:
        self._builders[provider.lower()] = builder

    def supports(self, provider: str) -> bool:
        return provider.lower() in self._builders

    def create(
        self,
        provider: str,
        config: Optional[Dict[str, Any]] = None,
        credentials: Optional[Dict[str, Any]] = None,
        connected: bool = False,
    ) -> Connector:
        """Crea un connector. `connected=False` (por defecto) = infraestructura
        lista pero SIN conectar a la API destino."""
        key = provider.lower()
        if key not in self._builders:
            raise ConnectorUnavailable(f"No se conoce el provider '{provider}'")
        return self._builders[key](
            config=config or {},
            credentials=credentials or {},
            connected=connected,
        )