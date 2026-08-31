from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from .base import Tool, ToolValidationError


class GmailSendTool(Tool):
    """Tool determinista de Gmail: envía/lee emails.

    En producción se conecta a la API real de Gmail usando las credenciales
    del tenant. Aquí simulamos el comportamiento con un mock determinista.
    """

    name = "gmail_send"

    def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        to = params.get("to", "")
        subject = params.get("subject", "")
        body = params.get("body", "")

        if not to or not subject:
            raise ToolValidationError("faltan campos: to y subject son obligatorios")

        return {
            "status": "SIMULATED",
            "real_execution": False,
            "to": to,
            "subject": subject,
            "body_preview": body[:80],
            "sent_at": datetime.utcnow().isoformat(),
            "message_id": f"gmail-{abs(hash(to + subject))}",
        }


class GmailReadTool(Tool):
    """Tool determinista de Gmail: lee emails del buzón del tenant."""

    name = "gmail_read"

    def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        query = params.get("query", "")
        max_results = int(params.get("max_results", 5))

        # Mock: devuelve 2 emails simulados
        return {
            "status": "SIMULATED",
            "real_execution": False,
            "query": query,
            "max_results": max_results,
            "messages": [
                {
                    "id": "msg-001",
                    "from": "cliente@empresa.com",
                    "subject": "Re: Presupuesto Q3",
                    "snippet": "Hola, aceptamos el presupuesto para el Q3...",
                },
                {
                    "id": "msg-002",
                    "from": "proveedor@logistica.com",
                    "subject": "Confirmación de envío",
                    "snippet": "Tu pedido 4829 ha sido enviado...",
                },
            ],
        }