from __future__ import annotations

import hashlib
import hmac
import json
import time
import uuid
from typing import Any, Callable, Dict, List, Optional

from ...connectors.core.models import CommandResult
from ...kernel.types.time import now_utc


class WebhookEvent:
    """Evento interno normalizado tras validar un webhook entrante."""

    def __init__(
        self,
        provider: str,
        event_type: str,
        external_id: str,
        payload: Dict[str, Any],
        workspace_id: Optional[str] = None,
    ):
        self.provider = provider
        self.event_type = event_type
        self.external_id = external_id
        self.payload = payload
        self.workspace_id = workspace_id
        self.received_at = now_utc()


class WebhookRegistry:
    """Registra handlers por tipo de evento de provider."""

    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}

    def register(self, event_type: str, handler: Callable) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    def handlers_for(self, event_type: str) -> List[Callable]:
        return self._handlers.get(event_type, [])


class WebhookValidator:
    """Verifica firmas HMAC, timestamps y replay protection."""

    def __init__(self, tolerance_s: int = 300):
        self.tolerance_s = tolerance_s
        self._seen_ids: set[str] = set()

    @staticmethod
    def verify_hmac_sha256(payload: bytes, signature: str, secret: str) -> bool:
        if not signature or not secret:
            return False
        expected = "sha256=" + hmac.new(
            secret.encode(), payload, hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

    @staticmethod
    def verify_hmac_sha1(payload: bytes, signature: str, secret: str) -> bool:
        if not signature or not secret:
            return False
        expected = "sha1=" + hmac.new(
            secret.encode(), payload, hashlib.sha1
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

    def verify_timestamp(self, ts: int | float) -> bool:
        now = int(time.time())
        return abs(now - int(ts)) <= self.tolerance_s

    def is_duplicate(self, event_id: str) -> bool:
        if event_id in self._seen_ids:
            return True
        self._seen_ids.add(event_id)
        if len(self._seen_ids) > 10000:
            self._seen_ids = set(list(self._seen_ids)[-5000:])
        return False


class WebhookReceiver:
    """Punto de entrada único para webhooks externos."""

    def __init__(
        self,
        registry: Optional[WebhookRegistry] = None,
        validator: Optional[WebhookValidator] = None,
    ):
        self.registry = registry or WebhookRegistry()
        self.validator = validator or WebhookValidator()

    def receive(
        self,
        provider: str,
        event_type: str,
        payload: Dict[str, Any],
        headers: Dict[str, str],
        secret: Optional[str] = None,
        signature_header: str = "X-Hub-Signature-256",
        timestamp_header: str = "X-Timestamp",
        event_id_header: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Procesa un webhook entrante.

        Si hay `secret` configurado, se EXIGE firma y se valida.
        Si no hay firma o es inválida, se rechaza.
        """
        raw = json.dumps(payload, sort_keys=True).encode()

        # ------------------------------------------------------------
        # 🔒 Si hay secreto configurado, EXIGIR firma
        # (corrige el bug que permitía procesar sin firma)
        # ------------------------------------------------------------
        if secret:
            sig = headers.get(signature_header, "")

            if not sig:
                return {
                    "status": "rejected",
                    "reason": "missing_signature",
                    "provider": provider,
                }

            if not WebhookValidator.verify_hmac_sha256(raw, sig, secret):
                return {
                    "status": "rejected",
                    "reason": "invalid_signature",
                    "provider": provider,
                }

        # Verificar timestamp (opcional)
        ts_str = headers.get(timestamp_header)
        if ts_str:
            try:
                if not self.validator.verify_timestamp(float(ts_str)):
                    return {
                        "status": "rejected",
                        "reason": "timestamp_out_of_tolerance",
                        "provider": provider,
                    }
            except ValueError:
                pass

        # Deduplicación (opcional)
        event_id = headers.get(event_id_header, "") if event_id_header else ""
        if not event_id:
            event_id = headers.get("X-Delivery", str(uuid.uuid4()))
        if self.validator.is_duplicate(event_id):
            return {"status": "duplicate", "event_id": event_id, "provider": provider}

        # Crear evento interno y despachar
        event = WebhookEvent(
            provider=provider,
            event_type=event_type,
            external_id=event_id,
            payload=payload,
        )

        results = []
        for handler in self.registry.handlers_for(event_type):
            try:
                handler(event)
                results.append({"handler": handler.__name__, "status": "ok"})
            except Exception as exc:
                results.append({
                    "handler": handler.__name__,
                    "status": "failed",
                    "error": str(exc)[:300],
                })

        # Si algún handler falló, reflejarlo en la respuesta
        failed = [r for r in results if r.get("status") == "failed"]
        if failed:
            return {
                "status": "handler_failed",
                "event_id": event_id,
                "provider": provider,
                "errors": failed,
            }

        return {"status": "processed", "event_id": event_id, "provider": provider}


class WebhookDispatcher:
    """Despacha eventos internos a los handlers registrados."""

    def __init__(self, registry: Optional[WebhookRegistry] = None):
        self.registry = registry or WebhookRegistry()

    def dispatch(self, event: WebhookEvent) -> List[CommandResult]:
        results = []
        for handler in self.registry.handlers_for(event.event_type):
            try:
                handler(event)
                results.append(
                    CommandResult(
                        ok=True,
                        output={"handler": handler.__name__, "status": "ok"},
                    )
                )
            except Exception as e:
                results.append(
                    CommandResult(
                        ok=False,
                        error=str(e)[:300],
                        error_type="WEBHOOK_DISPATCH_ERROR",
                    )
                )
        return results


# ------------------------------------------------------------
# Compatibilidad con el código existente
# ------------------------------------------------------------

def handle_webhook(payload: dict) -> dict:
    """Función legacy para compatibilidad con el stub anterior."""
    return {"status": "received", "payload": payload}


# Instancia global por defecto (para importación fácil)
default_receiver = WebhookReceiver()
default_dispatcher = WebhookDispatcher()