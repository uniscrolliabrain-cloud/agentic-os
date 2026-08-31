from __future__ import annotations
from pathlib import Path
from threading import RLock
from typing import List
from...kernel.world.events import Event
from.base import EventLogRepository

class JsonlEventLog(EventLogRepository):
    def __init__(self, base_dir: str | Path = "data/eventlog"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
    def _file_for(self, tenant_id: str) -> Path:
        return self.base_dir / f"{tenant_id}.jsonl"
    def append(self, event: Event) -> None:
        path = self._file_for(event.tenant_id)
        with self._lock:
            with open(path, "a", encoding="utf-8") as f:
                f.write(event.model_dump_json() + "\n")
    def list_for_tenant(self, tenant_id: str) -> List[Event]:
        path = self._file_for(tenant_id)
        if not path.exists():
            return []
        events = []
        with self._lock:
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    events.append(Event.model_validate_json(line))
        return events
    def list_all(self) -> List[Event]:
        events = []
        with self._lock:
            for file in self.base_dir.glob("*.jsonl"):
                for line in file.read_text(encoding="utf-8").splitlines():
                    if line.strip():
                        events.append(Event.model_validate_json(line))
        return events

    def all_events(self) -> List[Event]:
        """FASE 3.1: método común de interfaz (delegado en list_all)."""
        return self.list_all()
