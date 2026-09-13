from __future__ import annotations

import json
import logging
from threading import RLock
from typing import Any, Dict, List, Optional

from ...kernel.world.events import Event
from .base import EventLogRepository
from .jsonl import JsonlEventLog

logger = logging.getLogger(__name__)


class SupabaseEventLog(EventLogRepository):
    """EventLog via Supabase (PostgREST sobre el schema public.events).

    Es un wrapper de PostgresEventLog que usa la capa de abstraccin
    de Supabase en vez de psycopg directo. Ideal cuando se prefiere
    la API REST de Supabase sobre una conexin TCP directa.
    """

    def __init__(
        self,
        table: str = "events",
        schema: str = "public",
        base_dir: Optional[str] = None,
    ) -> None:
        self._lock = RLock()
        self._table = table
        self._schema = schema
        self._fallback: JsonlEventLog = JsonlEventLog(base_dir=base_dir) if base_dir else JsonlEventLog()
        self._client: Optional[Any] = None

    @property
    def available(self) -> bool:
        return self._get_client() is not None

    def _get_client(self) -> Optional[Any]:
        if self._client is not None:
            return self._client
        try:
            from .supabase_client import get_supabase
            client = get_supabase()
            self._client = client.db
            return self._client
        except Exception:
            logger.debug("Supabase not available, falling back to JSONL")
            return None

    def _table_ref(self) -> Any:
        client = self._get_client()
        if client is None:
            return None
        return client.table(self._table)

    def append(self, event: Event) -> None:
        if not self.available:
            self._fallback.append(event)
            return
        try:
            ref = self._table_ref()
            if ref is None:
                self._fallback.append(event)
                return
            ref.insert({
                "id": event.id,
                "kind": event.kind or "",
                "entity_id": event.entity_id,
                "tenant_id": event.tenant_id,
                "actor_id": event.actor_id or "",
                "payload": event.payload or {},
                "at": event.at.isoformat() if event.at else "",
                "correlation_id": event.correlation_id or "",
                "command_id": event.command_id or "",
            }).execute()
        except Exception:
            logger.exception("Supabase append failed; using fallback")
            self._fallback.append(event)

    def list_for_tenant(self, tenant_id: str) -> List[Event]:
        if not self.available:
            return self._fallback.list_for_tenant(tenant_id)
        try:
            ref = self._table_ref()
            if ref is None:
                return self._fallback.list_for_tenant(tenant_id)
            resp = ref.select("*").eq("tenant_id", tenant_id).order("at", desc=False).execute()
            return [self._row_to_event(row) for row in (resp.data or [])]
        except Exception:
            logger.exception("Supabase tenant read failed")
            return self._fallback.list_for_tenant(tenant_id)

    def list_all(self) -> List[Event]:
        if not self.available:
            return self._fallback.list_all()
        try:
            ref = self._table_ref()
            if ref is None:
                return self._fallback.list_all()
            resp = ref.select("*").order("at", desc=False).execute()
            return [self._row_to_event(row) for row in (resp.data or [])]
        except Exception:
            logger.exception("Supabase global read failed")
            return self._fallback.list_all()

    def all_events(self) -> List[Event]:
        return self.list_all()

    @staticmethod
    def _row_to_event(row: Dict[str, Any]) -> Event:
        payload = row.get("payload", {})
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError:
                payload = {}
        return Event(
            id=row.get("id", ""),
            kind=row.get("kind") or None,
            entity_id=row.get("entity_id", ""),
            tenant_id=row.get("tenant_id", ""),
            actor_id=row.get("actor_id") or None,
            payload=payload if isinstance(payload, dict) else {},
            at=row.get("at"),
            correlation_id=row.get("correlation_id") or None,
            command_id=row.get("command_id") or None,
        )
