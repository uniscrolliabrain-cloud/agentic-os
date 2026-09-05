"""Bug 13 - AuditLog.record() no persiste a disco: solo append en memoria"""

import json
import tempfile
from pathlib import Path

import pytest

from agentic_os.connectors.core.audit import AuditLog
from agentic_os.connectors.core.models import Command


def test_auditlog_persists_to_disk():
    """AuditLog.record() debe escribir el registro a disco, no solo en memoria."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "audit.jsonl"
        audit = AuditLog(log_path=str(log_path))

        cmd = Command(
            capability="email.message.send",
            params={"to": "test@example.com"},
            execution_id="exec-123",
            workspace_id="ws-1",
            actor_id="user-1",
        )
        audit.record(cmd, connector_id="gmail", provider="google", status="success")

        # Debe haber escrito al disco
        assert log_path.exists(), "AuditLog no escribió al disco"
        content = log_path.read_text()
        assert "email.message.send" in content, "El registro no contiene la capability"
        assert "exec-123" in content, "El registro no contiene el execution_id"


def test_auditlog_survives_instance_recreation():
    """Los registros deben sobrevivir a recrear la instancia AuditLog."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "audit.jsonl"

        # Crear instancia y registrar
        audit1 = AuditLog(log_path=str(log_path))
        cmd = Command(capability="file.read", params={"file_id": "f1"}, execution_id="exec-2")
        audit1.record(cmd, connector_id="drive", provider="google", status="success")

        # Recargar desde disco
        audit2 = AuditLog(log_path=str(log_path))
        records = audit2.all()
        assert len(records) >= 1, "Los registros no persisten entre instancias"


def test_auditlog_format_is_jsonl():
    """El formato de disco debe ser JSON Lines (un JSON por línea)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "audit.jsonl"
        audit = AuditLog(log_path=str(log_path))

        cmd = Command(capability="crm.contact.create", params={"name": "Juan"}, execution_id="exec-3")
        audit.record(cmd, connector_id="hubspot", provider="hubspot", status="success")

        content = log_path.read_text().strip()
        lines = content.split("\n")
        assert len(lines) >= 1, "Debe haber al menos una línea"
        # Cada línea debe ser JSON válido
        for line in lines:
            record = json.loads(line)
            assert "capability" in record
            assert "status" in record
