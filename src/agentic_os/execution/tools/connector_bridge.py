"""Puente ToolRegistry ↔ Connector Kernel (FASE 2 de hardening).

Unifica el camino de resolución de herramientas. Antes existían dos sistemas
que no se hablaban: execution/tools/registry.py (mocks usados por /api/execute)
y connectors/registry.py (CapabilityRegistry + ConnectorRouter, el kernel
documentado). Ahora la fuente de verdad de qué capabilities existen es el
Connector Kernel (ConnectorFactory + catálogo de providers): si la capability
canónica de una acción existe ahí, la resolución va SIEMPRE por
ConnectorRouter; los mocks de execution/tools/*.py son el fallback para
capabilities sin connector registrado.

Los agentes siguen sin ver credenciales, endpoints ni providers: solo reciben
el resultado normalizado.
"""

from __future__ import annotations

import asyncio
import logging
import threading
from typing import Any, Dict

from .base import Tool

logger = logging.getLogger(__name__)

# Alias acción del orquestador/mock -> capability canónica del Connector Kernel.
# Si el catálogo declara la capability, gana SIEMPRE el kernel.
CANONICAL_ALIASES: Dict[str, str] = {
    "gmail_send": "email.message.send",
    "gmail_read": "email.message.read",
    "slack_send": "communication.message.send",
    "slack_read": "communication.channel.read",
    "whatsapp_send": "whatsapp.message.send",
    "whatsapp_read": "whatsapp.message.receive",
    "calendar_create_event": "calendar.event.create",
    "calendar_list_events": "calendar.event.read",
    "web_scrape": "web.page.extract",
    "web_search": "web.search",
    "documentation_create": "knowledge.page.create",
    "documentation_search": "knowledge.page.search",
}


def _run_async(coro):
    """Ejecuta una corutina desde código síncrono de forma segura,
    incluso si el hilo actual ya tiene un event loop corriendo."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    box: Dict[str, Any] = {}

    def _runner() -> None:
        box["result"] = asyncio.run(coro)

    t = threading.Thread(target=_runner, daemon=True)
    t.start()
    t.join()
    return box.get("result")


class ConnectorBridgeError(Exception):
    """Fallo normalizado del Connector Kernel al ejecutar una capability."""

    def __init__(self, message: str, error_type: str = "UNKNOWN_ERROR", provider: Any = None):
        super().__init__(message)
        self.error_type = error_type
        self.provider = provider


class ConnectorBridgeTool(Tool):
    """Tool que resuelve a través del Connector Kernel (ConnectorRouter).

    Mantiene el nombre de la acción (p.ej. "gmail_send") para no romper la API,
    pero la ejecución real pasa por el camino canónico: Command pydantic ->
    CapabilityRegistry -> ConnectorRouter -> Connector -> resultado normalizado.
    """

    def __init__(self, name: str, capability: str, router: Any):
        self.name = name
        self.capability = capability
        self.router = router

    def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        dry_run = bool(params.get("dry_run", False))
        clean = {k: v for k, v in params.items() if k != "dry_run"}

        # Import local para evitar ciclos de importación
        from ...connectors.core.models import Command

        command = Command(
            capability=self.capability,
            params=clean,
            dry_run=dry_run,
        )
        result = _run_async(self.router.route(command))

        if result.ok:
            out: Dict[str, Any] = {
                "success": True,
                "via": "connector_kernel",
                "capability": self.capability,
            }
            if result.provider:
                out["provider"] = result.provider
            if result.dry_run:
                out["dry_run"] = True
                out["output"] = {"preview": result.preview}
            else:
                out["output"] = result.output if result.output is not None else (result.data or {})
            return out

        raise ConnectorBridgeError(
            message=f"{result.error_type or 'UNKNOWN_ERROR'}: {result.error or 'connector error'}",
            error_type=result.error_type or "UNKNOWN_ERROR",
            provider=result.provider,
        )


def _build_google_connector():
    """Intenta construir el GoogleConnector REAL si el flag y las credenciales
    están presentes. Devuelve None si no procede (→ stub como siempre).

    Gate doble: GOOGLE_REAL=true Y GOOGLE_CLIENT_ID/SECRET/REFRESH_TOKEN en
    Settings. Sin flag no se intenta nada (default producción-seguro).
    """
    from ...infrastructure.config.settings import settings

    if not getattr(settings, "google_real", False):
        return None
    if not (
        settings.google_client_id
        and settings.google_client_secret
        and settings.google_refresh_token
    ):
        return None
    try:
        from ...connectors.google import GoogleConnector

        conn = GoogleConnector()
        return conn if conn.connected else None
    except Exception:  # noqa: BLE001 — cualquier fallo de construcción → stub
        logger.exception("No se pudo construir GoogleConnector real; se usa stub")
        return None


def build_capability_registry():
    """Construye el CapabilityRegistry desde el catálogo de providers.

    Fuente de verdad de qué capabilities existen. Todos los connectors se
    crean SIN conectar (connected=False): la ejecución real devuelve
    CONNECTOR_NOT_CONFIGURED hasta que se configuren credenciales.

    Excepción: si GOOGLE_REAL=true y hay credenciales, Google registra el
    GoogleConnector real (Gmail/Drive/Calendar); las caps del spec que el
    adapter real no cubre (video/analytics) quedan en un stub residual con
    connector_id distinto ('google-extra') porque el registry reemplaza por id.
    """
    from ...connectors.factory import ConnectorFactory
    from ...connectors.providers import PROVIDER_SPECS, register_builtin_providers
    from ...connectors.registry import CapabilityRegistry

    factory = ConnectorFactory()
    register_builtin_providers(factory)
    registry = CapabilityRegistry()
    for provider_id in PROVIDER_SPECS:
        if not factory.supports(provider_id):
            continue
        if provider_id == "google":
            real = _build_google_connector()
            if real is not None:
                registry.register(real)
                spec_caps = PROVIDER_SPECS["google"]["caps"]
                extra = [c for c in spec_caps if c not in set(real.capabilities)]
                if extra:
                    residual = factory.create("google")
                    residual.connector_id = "google-extra"
                    residual.capabilities = extra
                    registry.register(residual)
                continue
        registry.register(factory.create(provider_id))
    return registry


def build_connector_router():
    from ...connectors.router import ConnectorRouter

    return ConnectorRouter(build_capability_registry())