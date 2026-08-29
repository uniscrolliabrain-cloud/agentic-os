"""infrastructure.persistence: event store y snapshots"""

from ..config.settings import settings
from .base import EventLogRepository
from .jsonl import JsonlEventLog
from .memory import InMemoryEventLog


def get_eventlog_repo() -> EventLogRepository:
    """Devuelve el repositorio de eventos según settings.eventlog_impl.

    Opciones: "memory" | "jsonl" (default) | "postgres".
    Postgres degrada a jsonl (fail-safe) si el driver/BD no está disponible,
    de modo que cambiar EVENTLOG_IMPL no rompe nunca el kernel.
    """
    impl = settings.eventlog_impl
    if impl == "postgres":
        from .postgres import PostgresEventLog

        repo = PostgresEventLog()
        return repo if repo.available else JsonlEventLog()
    if impl == "jsonl":
        return JsonlEventLog()
    return InMemoryEventLog()