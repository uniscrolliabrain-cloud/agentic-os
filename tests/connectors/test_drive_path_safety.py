"""Tests de aislamiento de paths para Google Drive (FASE 6).

Verifica que ``_safe_resolve`` rechaza escapes de directorio usando
comparación semántica (``pathlib.is_relative_to``) y no ``str.startswith``.
"""
from __future__ import annotations

import pytest

import agentic_os.execution.tools.drive_tool as drive_mod
from agentic_os.execution.tools.base import ToolValidationError
from agentic_os.execution.tools.drive_tool import (
    DriveListFilesTool,
    DriveReadFileTool,
    _safe_resolve,
    _tenant_drive_dir,
)


@pytest.fixture(autouse=True)
def _isolate_data_root(tmp_path, monkeypatch):
    # Iglora el layout real del repo: todo el drive se mapea a tmp_path.
    monkeypatch.setattr(drive_mod, "_DATA_ROOT", tmp_path)


def test_safe_subfolder_accepted(tmp_path):
    root = _tenant_drive_dir("t1")
    target = _safe_resolve(root, "subfolder")
    assert target == root.resolve() / "subfolder"


def test_tenant_root_evil_sibling_rejected(tmp_path):
    # root = <tmp>/tenants/acme/drive
    root = _tenant_drive_dir("acme")
    # Sibling que comparte prefijo de *string* con la raíz del tenant:
    # "<tmp>/tenants/acme/drive_evil/x".startswith("<tmp>/tenants/acme/drive") == True
    sibling = tmp_path / "tenants" / "acme" / "drive_evil"
    sibling.mkdir(parents=True)
    # El chequeo con str.startswith lo aceptaría (vulnerabilidad); is_relative_to lo rechaza.
    with pytest.raises(ToolValidationError):
        _safe_resolve(root, "../drive_evil/x")


def test_traversal_to_other_tenant_rejected(tmp_path):
    root = _tenant_drive_dir("t1")
    with pytest.raises(ToolValidationError):
        _safe_resolve(root, "../other-tenant")
    with pytest.raises(ToolValidationError):
        _safe_resolve(root, "../../etc/passwd")


def test_drive_list_files_rejects_traversal():
    with pytest.raises(ToolValidationError):
        DriveListFilesTool().run({"tenant_id": "t1", "folder": "../other-tenant"})


def test_drive_read_file_rejects_traversal_and_allows_legit(tmp_path):
    root = _tenant_drive_dir("t1")
    (root / "ok.txt").write_text("hola", encoding="utf-8")
    # escape → rechazado
    with pytest.raises(ToolValidationError):
        DriveReadFileTool().run({"tenant_id": "t1", "path": "../other-tenant/secret"})
    # acceso legítimo dentro del root → ok
    res = DriveReadFileTool().run({"tenant_id": "t1", "path": "ok.txt"})
    assert res["content"] == "hola"
    assert res["status"] == "SIMULATED"
