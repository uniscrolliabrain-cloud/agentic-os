from..config.settings import settings
from.base import EventLogRepository
from.jsonl import JsonlEventLog
from.memory import InMemoryEventLog

def get_eventlog_repo() -> EventLogRepository:
    if settings.eventlog_impl == "jsonl":
        return JsonlEventLog()
    return InMemoryEventLog()