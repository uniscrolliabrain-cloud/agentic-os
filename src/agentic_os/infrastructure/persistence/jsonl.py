from __future__ import annotations

import re
from pathlib import Path
from threading import RLock
from typing import List

from ...kernel.world.events import Event
from .base import EventLogRepository

# El tenant_id identifica un fichero en disco: solo se admiten caracteres
# seguros (sin barras ni "..") para impedir path traversal en el event log.
_TENANT_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{1,64}$")


class JsonlEventLog(EventLogRepository):
    def __init__(self, base_dir: str | Path = "data/eventlog"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()

    @staticmethod
    def _validate_tenant_id(tenant_id: str) -> None:
        """Rechaza tenant_ids que no cumplan el patrón seguro (fail-closed)."""
        if not isinstance(tenant_id, str) or not _TENANT_ID_RE.fullmatch(tenant_id):
            raise ValueError(
                f"tenant_id '{tenant_id}' no válido: solo [a-z0-9_-] (2-65 "
                f"caracteres), sin barras ni path traversal"
            )

    def _file_for(self, tenant_id: str) -> Path:
        self._validate_tenant_id(tenant_id)
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
                # Solo se leen ficheros cuyo nombre cumple el patrón de tenant
                # (bloquea lecturas de ficheros ajenos / path traversal).
                if not _TENANT_ID_RE.fullmatch(file.stem):
                    continue
                for line in file.read_text(encoding="utf-8").splitlines():
                    if line.strip():
                        events.append(Event.model_validate_json(line))
        return events

    def all_events(self) -> List[Event]:
        """FASE 3.1: método común de interfaz (delegado en list_all)."""
        return self.list_all()
