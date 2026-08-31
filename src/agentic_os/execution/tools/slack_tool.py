from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from .base import Tool, ToolValidationError


class SlackSendTool(Tool):
    """Tool determinista de Slack: envía mensaje a un canal/usuario."""

    name = "slack_send"

    def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        channel = params.get("channel", "")
        text = params.get("text", "")

        if not channel or not text:
            raise ToolValidationError("faltan campos: channel y text son obligatorios")

        return {
            "status": "enviado",
            "channel": channel,
            "text_preview": text[:80],
            "sent_at": datetime.utcnow().isoformat(),
            "ts": f"slack-{abs(hash(channel + text))}",
        }


class SlackReadTool(Tool):
    """Tool determinista de Slack: lee mensajes recientes de un canal."""

    name = "slack_read"

    def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        channel = params.get("channel", "")
        limit = int(params.get("limit", 5))

        return {
            "status": "leido",
            "channel": channel,
            "limit": limit,
            "messages": [
                {"user": "U1234", "ts": "1750000000.0001", "text": "Hola equipo, ¿avanzamos con el informe?"},
                {"user": "U5678", "ts": "1750000020.0002", "text": "Sí, lo tengo casi listo."},
            ],
        }