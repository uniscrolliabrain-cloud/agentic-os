from __future__ import annotations

"""interfaces/api/webhooks.py - Re-exporta el canonical webhook implementation.

La implementacion canonica vive en connectors/webhook/__init__.py.
Este modulo re-exporta las clases para compatibilidad con el codigo
que importa desde interfaces.api.webhooks.
"""

from ...connectors.webhook import (
    WebhookEvent,
    WebhookRegistry,
    WebhookValidator,
    WebhookReceiver,
    WebhookDispatcher,
)
from ...connectors.core.models import CommandResult


# ------------------------------------------------------------
# Compatibilidad con el codigo existente
# ------------------------------------------------------------

def handle_webhook(payload: dict) -> dict:
    """Funcion legacy para compatibilidad con el stub anterior."""
    return {"status": "received", "payload": payload}


# Instancia global por defecto (para importacion facil)
default_receiver = WebhookReceiver()
default_dispatcher = WebhookDispatcher()