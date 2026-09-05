from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from ...kernel.types.time import now_utc

from ..core.models import Command


class AuditRecord(BaseModel):
    model_config = {"from_attributes": True}

    audit_id: str = Field(default_factory=lambda: str(uuid4()))
    workspace_id: Optional[str] = None
    actor_id: Optional[str] = None
    command_id: Optional[str] = None
    capability: str
    connector_id: Optional[str] = None
    provider: Optional[str] = None
    operation: str
    target: Optional[str] = None
    status: str
    timestamp: datetime = Field(default_factory=now_utc)
    approval_reference: Optional[str] = None
    duration_ms: int = 0


class AuditLog:
    """Log de auditoría de efectos externos. Nunca almacena secrets."""

    def __init__(self, log_path: Optional[str] = None):
        self.log_path = log_path
        self._records: List[AuditRecord] = []
        self._load_from_disk()

    def record(self, command: Command, connector_id: str, provider: str,
               status: str, duration_ms: int = 0,
               approval_reference: Optional[str] = None) -> AuditRecord:
        record = AuditRecord(
            audit_id=str(uuid4()),
            workspace_id=command.workspace_id,
            actor_id=command.actor_id,
            command_id=command.execution_id,
            capability=command.capability,
            connector_id=connector_id,
            provider=provider,
            operation=f"{provider}::{command.capability}",
            target=str(command.params.get("target", ""))[:200] if command.params else "",
            status=status,
            approval_reference=approval_reference,
            duration_ms=duration_ms,
        )
        self._records.append(record)
        # Persistir a disco (JSONL) — solo referencias de auditoría, nunca secrets
        self._persist_record(record)
        return record

    def _persist_record(self, record: AuditRecord) -> None:
        """Escribe el registro a disco en formato JSONL."""
        if not self.log_path:
            return
        import json
        from pathlib import Path
        Path(self.log_path).parent.mkdir(parents=True, exist_ok=True)
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(record.model_dump_json() + "\n")

    def _load_from_disk(self) -> None:
        """Carga registros previos del disco al iniciar."""
        if not self.log_path:
            return
        from pathlib import Path
        if not Path(self.log_path).exists():
            return
        import json
        with open(self.log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        data = json.loads(line)
                        self._records.append(AuditRecord(**data))
                    except Exception:
                        pass

    def all(self) -> List[Any]:
        return list(self._records)
