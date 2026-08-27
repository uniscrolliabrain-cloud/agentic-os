from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from ..core.models import Command


class AuditRecord(BaseModel := Any):
    audit_id: str
    workspace_id: Optional[str]
    actor_id: Optional[str]
    command_id: Optional[str]
    capability: str
    connector_id: Optional[str]
    provider: Optional[str]
    operation: str
    target: Optional[str]
    status: str
    timestamp: datetime = None
    approval_reference: Optional[str] = None
    duration_ms: int = 0

    def __init__(self, **data):
        data.setdefault("timestamp", datetime.utcnow())
        data.setdefault("audit_id", str(uuid4()))
        super().__init__(**data)


class AuditLog:
    """Log de auditoría de efectos externos. Nunca almacena secrets."""

    def __init__(self, log_path: Optional[str] = None):
        self.log_path = log_path
        self._records: List[AuditRecord] = []

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
        # persistir solo referencias de auditoría, nunca secrets
        import json
        from pathlib import Path

        Path(self.log_path).parent.mkdir(parents=True, exist_ok=True) if self.log_path else None
        return record

    def all(self) -> List[Any]:
        return list(self._records)
