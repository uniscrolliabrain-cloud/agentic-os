"""Persistencia Postgres para el EventLog (FASE 3).

Implementa EventLogRepository (Protocol de base.py) sobre una tabla `events`.
Thread-safe con RLock. Las queries son SIEMPRE parametrizadas (nunca SQL
generado por el LLM). Si el driver o la base de datos no está disponible,
NO rompe el kernel: emite un aviso y se degrada a JsonlEventLog (fail-safe);
el orchestrator y el executor nunca dependen de esto directamente.

Config:
    EVENTLOG_IMPL=postgres
    POSTGRES_DSN=postgresql://user:pass@host:5432/db
"""

from __future__ import annotations

import logging
import os
from threading import RLock
from typing import Any, List, Optional

from ...kernel.world.events import Event
from .base import EventLogRepository
from .jsonl import JsonlEventLog

logger = logging.getLogger(__name__)

_DSN_ENV = "POSTGRES_DSN"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id         TEXT PRIMARY KEY,
    kind       TEXT NOT NULL,
    entity_id  TEXT NOT NULL,
    tenant_id  TEXT NOT NULL,
    actor_id   TEXT,
    payload    TEXT NOT NULL DEFAULT '{}',
    at         TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_events_tenant ON events (tenant_id, at);
"""


def _load_driver():
    """Devuelve el driver postgres (psycopg/psycopg2) o None si no está instalado."""
    try:
        import psycopg  # type: ignore
        return psycopg
    except ImportError:
        try:
            import psycopg2  # type: ignore
            return psycopg2
        except ImportError:
            return None


class PostgresEventLog(EventLogRepository):
    """Repositorio de eventos en PostgreSQL (aislado por tenant_id)."""

    def __init__(self, dsn: Optional[str] = None, base_dir: Optional[str] = None):
        self._lock = RLock()
        self.dsn = dsn or os.environ.get(_DSN_ENV) or ""
        self._driver = _load_driver()
        # fail-safe si la BD no responde; base_dir permite aislar en tests
        self._fallback = JsonlEventLog(base_dir=base_dir) if base_dir else JsonlEventLog()
        if not self.dsn or self._driver is None:
            logger.warning(
                "PostgresEventLog sin driver '%s' o DSN vacio -> usando fallback JSONL",
                self._driver.__name__ if self._driver else "no-driver",
            )

    @property
    def available(self) -> bool:
        return bool(self._driver and self.dsn)

    # ------------------------------------------------------- helpers -------
    def _connect(self):
        return self._driver.connect(self.dsn)

    def _ensure_schema(self, conn) -> None:
        with conn.cursor() as cur:
            cur.execute(_SCHEMA)
        conn.commit()

    # --------------------------------------------------------- protocol ----
    def append(self, event: Event) -> None:
        if not self.available:
            self._fallback.append(event)
            return
        with self._lock:
            try:
                with self._connect() as conn:
                    self._ensure_schema(conn)
                    payload = event.payload
                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            INSERT INTO events (id, kind, entity_id, tenant_id, actor_id, payload, at)
                            VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s)
                            ON CONFLICT (id) DO NOTHING
                            """,
                            (event.id, event.kind, event.entity_id, event.tenant_id,
                             event.actor_id, payload, event.at),
                        )
                    conn.commit()
            except Exception as exc:  # noqa: BLE001 - fail-safe, nunca romper kernel
                logger.error("Postgres append fallo: %s", exc)
                self._fallback.append(event)

    def list_for_tenant(self, tenant_id: str) -> List[Event]:
        if not self.available:
            return self._fallback.list_for_tenant(tenant_id)
        with self._lock:
            try:
                with self._connect() as conn:
                    self._ensure_schema(conn)
                    with conn.cursor() as cur:
                        cur.execute(
                            "SELECT id, kind, entity_id, tenant_id, actor_id, payload, at "
                            "FROM events WHERE tenant_id = %s ORDER BY at ASC",
                            (tenant_id,),
                        )
                        rows = cur.fetchall()
                return [self._row_to_event(r) for r in rows]
            except Exception as exc:  # noqa: BLE001
                logger.error("Postgres list_for_tenant fallo: %s", exc)
                return self._fallback.list_for_tenant(tenant_id)

    def list_all(self) -> List[Event]:
        if not self.available:
            return self._fallback.list_all()
        with self._lock:
            try:
                with self._connect() as conn:
                    self._ensure_schema(conn)
                    with conn.cursor() as cur:
                        cur.execute(
                            "SELECT id, kind, entity_id, tenant_id, actor_id, payload, at "
                            "FROM events ORDER BY at ASC"
                        )
                        rows = cur.fetchall()
                return [self._row_to_event(r) for r in rows]
            except Exception as exc:  # noqa: BLE001
                logger.error("Postgres list_all fallo: %s", exc)
                return self._fallback.list_all()

    # ------------------------------------------------------- helpers -------
    @staticmethod
    def _row_to_event(row: Any) -> Event:
        import json

        payload = row[5]
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except Exception:  # noqa: BLE001
                payload = {}
        return Event(
            id=row[0],
            kind=row[1],
            entity_id=row[2],
            tenant_id=row[3],
            actor_id=row[4],
            payload=payload if isinstance(payload, dict) else {},
            at=row[6],
        )


# Si no hay driver instalado, exponer el fallback igualmente para que la
# factory nunca importe con error.
_DRIVER_AVAILABLE = _load_driver() is not None