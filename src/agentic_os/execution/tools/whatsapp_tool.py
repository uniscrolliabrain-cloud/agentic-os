from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from .base import Tool


class WhatsAppSendTool(Tool):
    """Tool determinista de WhatsApp: envía mensaje a un contacto."""

    name = "whatsapp_send"

    def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        to = params.get("to", "")
        text = params.get("text", "")

        if not to or not text:
            return {"error": "faltan campos: to y text son obligatorios"}

        return {
            "status": "enviado",
            "to": to,
            "text_preview": text[:80],
            "sent_at": datetime.utcnow().isoformat(),
            "message_id": f"wa-{abs(hash(to + text))}",
        }


class WhatsAppReadTool(Tool):
    """Tool determinista de WhatsApp: lee conversaciones recientes."""

    name = "whatsapp_read"

    def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        contact = params.get("contact", "")
        limit = int(params.get("limit", 5))

        return {
            "status": "leido",
            "contact": contact,
            "limit": limit,
            "messages": [
                {"from": "cliente", "text": "Hola, ¿disponible mañana a las 10?"},
                {"from": "agente", "text": "Sí, perfecto. ¿Te confirmo la cita?"},
            ],
        }