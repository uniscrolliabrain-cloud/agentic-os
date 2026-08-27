"""CapabilityRegistry: registra connectors, sus capacidades y resuelve cuáles
soportan una capability canónica (sin exponer detalle del provider a los agentes)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .core.base import Connector


class CapabilityRegistry:
    """Mapa capability canónica → connectors que la soportan."""

    def __init__(self) -> None:
        self._connectors: Dict[str, Connector] = {}
        self._capability_index: Dict[str, List[str]] = {}  # capability -> [connector_id]

    # ------------------------------------------------------------ registro ---
    def register(self, connector: Connector) -> None:
        cid = connector.connector_id
        previous = self._connectors.get(cid)
        if previous:
            # quitar del índice sus capabilities anteriores
            for cap in previous.capabilities:
                ids = self._capability_index.get(cap, [])
                if cid in ids:
                    ids.remove(cid)
        self._connectors[cid] = connector
        for cap in connector.capabilities:
            self._capability_index.setdefault(cap, [])
            if cid not in self._capability_index[cap]:
                self._capability_index[cap].append(cid)

    def unregister(self, connector_id: str) -> Optional[Connector]:
        conn = self._connectors.pop(connector_id, None)
        if conn:
            for cap in conn.capabilities:
                ids = self._capability_index.get(cap, [])
                if connector_id in ids:
                    ids.remove(connector_id)
        return conn

    # --------------------------------------------------------- consultas ---
    def list_providers(self) -> List[str]:
        return sorted({c.provider for c in self._connectors.values()})

    def list_connectors(self) -> List[Connector]:
        return list(self._connectors.values())

    def get_connector(self, connector_id: str) -> Optional[Connector]:
        return self._connectors.get(connector_id)

    def resolve(self, capability: str) -> List[Connector]:
        """Devuelve todos los connectors que soportan la capability."""
        ids = self._capability_index.get(capability, [])
        return [self._connectors[cid] for cid in ids if cid in self._connectors]

    def has_capability(self, capability: str) -> bool:
        return bool(self._capability_index.get(capability))

    def health_of(self, connector_id: str) -> Any:
        conn = self._connectors.get(connector_id)
        return conn.health_check() if conn else None