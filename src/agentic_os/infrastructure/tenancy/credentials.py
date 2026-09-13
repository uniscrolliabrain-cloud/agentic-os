"""Credenciales por cliente final (FASE 2 — PLAN_AGENCIA_TENANT.md).

El tenant es la agencia; las credenciales de cada cliente final viven en
``TenantConfig.credentials["clients"]`` con esta forma::

    {
        "api_key": "tk_...dedicado a la agencia...",
        "clients": {
            "<client_id>": {
                "name": "Clinica XYZ",
                "providers": {
                    "google": {"refresh_token": "...", ...},
                    "hubspot": {"access_token": "..."},
                },
            }
        },
    }

Invariantes de seguridad:

- El agente JAMAS ve estos secretos: solo declara ``client_id`` en el
  ``Command`` y el router resuelve las credenciales fuera de su vista.
- Esta funcion NUNCA loguea valores de credenciales: solo nombres de
  provider y existencia/ausencia.
- Sin credenciales para el par (client_id, provider) se devuelve ``None``
  y el conector queda en stub (``CONNECTOR_NOT_CONFIGURED``); nunca se
  inventan credenciales ni se cae a globales.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def resolve_client_credentials(
    tenant: Any,
    client_id: str,
    provider: str,
) -> Optional[Dict[str, Any]]:
    """Resuelve las credenciales de un provider para un cliente final.

    Args:
        tenant: ``Tenant`` (o cualquier objeto con ``.slug`` y
            ``.config.credentials``) de la agencia.
        client_id: identificador del cliente final (slug de ``AgencyClient``).
        provider: nombre del provider (p. ej. ``"google"``, ``"hubspot"``).

    Returns:
        Dict copiado con las credenciales, o ``None`` si no existen.
        La copia evita que el caller mute el registry en memoria.
    """
    if not client_id or not provider:
        return None
    credentials = getattr(getattr(tenant, "config", None), "credentials", None)
    if not isinstance(credentials, dict):
        return None
    clients = credentials.get("clients")
    if not isinstance(clients, dict):
        return None
    entry = clients.get(client_id)
    if not isinstance(entry, dict):
        logger.debug(
            "sin credenciales: tenant=%s client=%s provider=%s (cliente desconocido)",
            getattr(tenant, "slug", "?"),
            client_id,
            provider,
        )
        return None
    providers = entry.get("providers")
    if not isinstance(providers, dict):
        return None
    creds = providers.get(provider)
    if not isinstance(creds, dict) or not creds:
        logger.debug(
            "sin credenciales: tenant=%s client=%s provider=%s (no configurado)",
            getattr(tenant, "slug", "?"),
            client_id,
            provider,
        )
        return None
    return dict(creds)


__all__ = ["resolve_client_credentials"]
