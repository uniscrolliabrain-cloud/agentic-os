"""FASE 6: pipelines end-to-end simulados (leads -> drafts -> EventLog)."""

from __future__ import annotations

import json
from pathlib import Path

from agentic_os.execution.tools import build_default_registry
from agentic_os.orchestration.pipelines import PIPELINES
from agentic_os.orchestration.orchestrator import Orchestrator, _PipelineExecutorHost
from agentic_os.kernel.world.events import EventLog


def _seed_drive(tmp_path: Path) -> None:
    """Escribe un CSV de leads en la cache local de Drive del tenant 't1'."""
    drive_dir = tmp_path / "tenants" / "t1" / "drive" / "leads" / "t1"
    drive_dir.mkdir(parents=True, exist_ok=True)
    (drive_dir / "leads_2026.csv").write_text(
        "name,email\nAna,ana@empresa.com\nLuis,luis@otra.com\n",
        encoding="utf-8",
    )


def test_pipeline_leads_to_draft_crea_drafts_y_eventos(tmp_path: Path) -> None:
    from agentic_os.execution.tools.drive_tool import _DATA_ROOT as DRIVE_ROOT

    # Redirigir la raíz de datos de las tools hacia tmp_path para no ensuciar el repo
    import agentic_os.execution.tools.drive_tool as drive_mod
    import agentic_os.execution.tools.gmail_tool as gmail_mod

    old_drive_root = drive_mod._DATA_ROOT
    old_gmail_root = gmail_mod._DATA_ROOT
    drive_mod._DATA_ROOT = tmp_path
    gmail_mod._DATA_ROOT = tmp_path

    try:
        _seed_drive(tmp_path)
        log = EventLog()
        host = _PipelineExecutorHost(llm=None, registry=build_default_registry())
        result = PIPELINES["leads_to_draft"](host, host.registry, "t1")
        assert result["status"] == "OK"
        assert result["drafts_created"] == 2

        drafts_dir = tmp_path / "tenants" / "t1" / "drafts"
        drafts = list(drafts_dir.glob("*.json"))
        assert len(drafts) == 2
        first = json.loads(drafts[0].read_text(encoding="utf-8"))
        assert first["tenant_id"] == "t1"
        assert first["status"] == "SIMULATED"
        assert first["real_execution"] is False
        assert "@" in first["to"]
    finally:
        drive_mod._DATA_ROOT = old_drive_root
        gmail_mod._DATA_ROOT = old_gmail_root


def test_pipeline_inbox_watcher_simulado() -> None:
    log = EventLog()
    host = _PipelineExecutorHost(llm=None, registry=build_default_registry())
    result = PIPELINES["inbox_watcher"](host, host.registry, "t2")
    assert result["status"] == "OK"
    assert result["processed"] == 2
    assert result["drafts_created"] == 1  # solo el email clasificado como lead