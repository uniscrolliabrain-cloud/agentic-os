from __future__ import annotations

import json
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
    id              TEXT PRIMARY KEY,
    kind            TEXT NOT NULL,
    entity_id       TEXT NOT NULL,
    tenant_id       TEXT NOT NULL,
    actor_id        TEXT,
    payload         JSONB NOT NULL DEFAULT '{}',
    at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    correlation_id  TEXT,
    command_id      TEXT
);

CREATE INDEX IF NOT EXISTS idx_events_tenant
    ON events (tenant_id, at);

CREATE INDEX IF NOT EXISTS idx_events_correlation
    ON events (tenant_id, correlation_id);

CREATE INDEX IF NOT EXISTS idx_events_command
    ON events (tenant_id, command_id);
"""


def _load_driver():
    try:
        import psycopg
        return psycopg
    except ImportError:
        try:
            import psycopg2
            return psycopg2
        except ImportError:
            return None


# Flag de disponibilidad del driver, expuesto para tests de degradación.
_DRIVER_AVAILABLE = _load_driver() is not None


class PostgresEventLog(EventLogRepository):

    def __init__(
        self,
        dsn: Optional[str] = None,
        base_dir: Optional[str] = None,
    ):
        self._lock = RLock()
        self.dsn = dsn or os.environ.get(_DSN_ENV) or ""
        self._driver = _load_driver()

        self._fallback = (
            JsonlEventLog(base_dir=base_dir)
            if base_dir
            else JsonlEventLog()
        )

    @property
    def available(self) -> bool:
        return bool(self._driver and self.dsn)

    def _connect(self):
        return self._driver.connect(self.dsn)

    def _ensure_schema(self, conn) -> None:
        with conn.cursor() as cursor:
            cursor.execute(_SCHEMA)

            # Migración segura para instalaciones existentes.
            cursor.execute(
                """
                ALTER TABLE events
                ADD COLUMN IF NOT EXISTS correlation_id TEXT
                """
            )

            cursor.execute(
                """
                ALTER TABLE events
                ADD COLUMN IF NOT EXISTS command_id TEXT
                """
            )

        conn.commit()

    def append(self, event: Event) -> None:

        if not self.available:
            self._fallback.append(event)
            return

        with self._lock:
            try:
                with self._connect() as conn:
                    self._ensure_schema(conn)

                    with conn.cursor() as cursor:
                        cursor.execute(
                            """
                            INSERT INTO events (
                                id,
                                kind,
                                entity_id,
                                tenant_id,
                                actor_id,
                                payload,
                                at,
                                correlation_id,
                                command_id
                            )
                            VALUES (
                                %s,
                                %s,
                                %s,
                                %s,
                                %s,
                                %s::jsonb,
                                %s,
                                %s,
                                %s
                            )
                            ON CONFLICT (id) DO NOTHING
                            """,
                            (
                                event.id,
                                event.kind,
                                event.entity_id,
                                event.tenant_id,
                                event.actor_id,
                                json.dumps(
                                    event.payload,
                                    ensure_ascii=False,
                                ),
                                event.at,
                                event.correlation_id,
                                event.command_id,
                            ),
                        )

                    conn.commit()

            except Exception:
                logger.exception(
                    "Postgres append failed; using fallback"
                )
                self._fallback.append(event)

    def list_for_tenant(
        self,
        tenant_id: str,
    ) -> List[Event]:

        if not self.available:
            return self._fallback.list_for_tenant(tenant_id)

        with self._lock:
            try:
                with self._connect() as conn:
                    self._ensure_schema(conn)

                    with conn.cursor() as cursor:
                        cursor.execute(
                            """
                            SELECT
                                id,
                                kind,
                                entity_id,
                                tenant_id,
                                actor_id,
                                payload,
                                at,
                                correlation_id,
                                command_id
                            FROM events
                            WHERE tenant_id = %s
                            ORDER BY at ASC
                            """,
                            (tenant_id,),
                        )

                        rows = cursor.fetchall()

                return [
                    self._row_to_event(row)
                    for row in rows
                ]

            except Exception:
                logger.exception(
                    "Postgres tenant read failed"
                )
                return self._fallback.list_for_tenant(
                    tenant_id
                )

    def list_all(self) -> List[Event]:

        if not self.available:
            return self._fallback.list_all()

        with self._lock:
            try:
                with self._connect() as conn:
                    self._ensure_schema(conn)

                    with conn.cursor() as cursor:
                        cursor.execute(
                            """
                            SELECT
                                id,
                                kind,
                                entity_id,
                                tenant_id,
                                actor_id,
                                payload,
                                at,
                                correlation_id,
                                command_id
                            FROM events
                            ORDER BY at ASC
                            """
                        )

                        rows = cursor.fetchall()

                return [
                    self._row_to_event(row)
                    for row in rows
                ]

            except Exception:
                logger.exception(
                    "Postgres global read failed"
                )
                return self._fallback.list_all()

    def all_events(self) -> List[Event]:
        return self.list_all()

    @staticmethod
    def _row_to_event(row: Any) -> Event:

        payload = row[5]

        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError:
                payload = {}

        return Event(
            id=row[0],
            kind=row[1],
            entity_id=row[2],
            tenant_id=row[3],
            actor_id=row[4],
            payload=payload if isinstance(payload, dict) else {},
            at=row[6],
            correlation_id=row[7],
            command_id=row[8],
        )
