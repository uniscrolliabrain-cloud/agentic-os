"""Sistema de webhooks: recepción, validación y despacho.

Pipeline:
  WEBHOOK → AUTHENTICATE → VERIFY SIGNATURE → VALIDATE PAYLOAD →
  IDENTIFY PROVIDER → MAP EVENT → CREATE INTERNAL EVENT → DISPATCH
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from ..core.models import CommandResult
from ...kernel.types.time import now_utc

logger = logging.getLogger(__name__)


class WebhookEvent(BaseModel):
    """Evento interno normalizado tras validar un webhook entrante.

    Modelo Pydantic v2 real: valida tipos y rechaza datos inesperados.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    provider: Optional[str] = None
    event_id: str
    event_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    received_at: datetime = Field(
        default_factory=now_utc,
    )
    workspace_id: Optional[str] = None


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
    def verify_hmac_sha256(
        payload: bytes, signature: str, secret: str
    ) -> bool:
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

    def __init__(self, registry: Optional[WebhookRegistry] = None,
                 validator: Optional[WebhookValidator] = None):
        self.registry = registry or WebhookRegistry()
        self.validator = validator or WebhookValidator()

    def receive(
        self,
        provider: str,
        event_type: str,
        payload: Dict[str, Any],
        headers: Dict[str, str],
        secret_env_key: Optional[str] = None,
        signature_header: str = "X-Hub-Signature-256",
        timestamp_header: str = "X-Timestamp",
        event_id_header: Optional[str] = None,
    ) -> Dict[str, Any]:
        raw = json.dumps(payload, sort_keys=True).encode()

        # verify signature
        sig = headers.get(signature_header, "")
        secret = self._get_secret(secret_env_key)
        if secret and sig:
            if not WebhookValidator.verify_hmac_sha256(raw, sig, secret):
                return {"status": "rejected", "reason": "invalid_signature"}

        # verify timestamp
        ts_str = headers.get(timestamp_header)
        if ts_str:
            try:
                if not self.validator.verify_timestamp(float(ts_str)):
                    return {"status": "rejected", "reason": "timestamp_out_of_tolerance"}
            except ValueError:
                pass

        # dedup
        event_id = headers.get(event_id_header, "") if event_id_header else ""
        if not event_id:
            event_id = headers.get("X-Delivery", str(uuid.uuid4()))
        if self.validator.is_duplicate(event_id):
            return {"status": "duplicate", "event_id": event_id}

        # create internal event + dispatch
        event = WebhookEvent(
            provider=provider,
            event_type=event_type,
            event_id=event_id,
            payload=payload,
        )
        handler_errors: list[str] = []
        for handler in self.registry.handlers_for(event_type):
            try:
                handler(event)
            except Exception as exc:  # noqa: BLE001
                # NO error silencioso: registrar y exponer en la respuesta.
                logger.warning(
                    "webhook handler %s falló para %s: %s",
                    getattr(handler, "__name__", handler),
                    event_id,
                    exc,
                    exc_info=exc,
                )
                handler_errors.append(f"{getattr(handler, '__name__', 'handler')}: {exc}")
        result: dict = {"status": "processed", "event_id": event_id}
        if handler_errors:
            result["handler_errors"] = handler_errors
        return result

    def _get_secret(self, env_key: Optional[str]) -> Optional[str]:
        if not env_key:
            return None
        import os

        return os.environ.get(env_key)


class WebhookDispatcher:
    """Despacha eventos internos a los handlers registrados."""

    def __init__(self, registry: Optional[WebhookRegistry] = None):
        self.registry = registry or WebhookRegistry()

    def dispatch(self, event: "WebhookEvent") -> List[CommandResult]:
        results = []
        for handler in self.registry.handlers_for(event.event_type):
            try:
                handler(event)
            except Exception as e:
                results.append(
                    CommandResult(
                        ok=False,
                        error=str(e),
                        error_type="WEBHOOK_DISPATCH_ERROR",
                    )
                )
        return results
