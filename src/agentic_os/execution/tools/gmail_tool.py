from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from .base import Tool, ToolValidationError

_DATA_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent / "data"


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


class GmailCreateDraftTool(Tool):
    """Crea un borrador de email en data/tenants/{tenant_id}/drafts/ (FASE 6).

    SIMULADO y preparado para la fase real: nunca envía nada. Guarda el borrador
    como JSON en la carpeta de drafts del tenant (fuente de verdad de borradores).
    """

    name = "gmail_create_draft"

    def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        from pathlib import Path
        import json
        import uuid

        tenant_id = params.get("tenant_id", "")
        to = params.get("to", "")
        subject = params.get("subject", "")
        body = params.get("body", "")

        if not tenant_id:
            raise ToolValidationError("faltan campos: tenant_id es obligatorio")
        if not to or not subject:
            raise ToolValidationError("faltan campos: to y subject son obligatorios")

        data_root = _DATA_ROOT
        drafts_dir = data_root / "tenants" / tenant_id / "drafts"
        drafts_dir.mkdir(parents=True, exist_ok=True)
        draft_id = f"drf_{uuid.uuid4().hex[:10]}"
        draft = {
            "id": draft_id,
            "tenant_id": tenant_id,
            "to": to,
            "subject": subject,
            "body": body,
            "created_at": datetime.utcnow().isoformat(),
            "status": "SIMULATED",
            "real_execution": False,
        }
        (drafts_dir / f"{draft_id}.json").write_text(
            json.dumps(draft, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return draft


class GmailListUnreadTool(Tool):
    """Lista emails no leídos (simulado). Clasificación posterior con LLM."""

    name = "gmail_list_unread"

    def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        max_results = int(params.get("max_results", 3))
        return {
            "status": "SIMULATED",
            "real_execution": False,
            "messages": [
                {
                    "id": "unread-001",
                    "from": "lead@empresa.com",
                    "subject": "Quiero un presupuesto para tu producto",
                    "snippet": "Somos una empresa de logística y queremos...",
                },
                {
                    "id": "unread-002",
                    "from": "soporte@cliente.com",
                    "subject": "Problema con la factura",
                    "snippet": "Hola, no me llega la factura numero 1281...",
                },
            ][: max_results],
        }