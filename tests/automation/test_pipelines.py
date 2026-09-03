"""FASE 6: pipelines end-to-end simulados (leads -> drafts -> EventLog).

Los pipelines se ejecutan SIEMPRE vía PipelineRunner -> Executor -> Policy ->
Tool -> EventLog (camino canónico, nunca llamadas directas a Tool).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentic_os.execution.executor import Executor
from agentic_os.execution.tools import build_default_registry
from agentic_os.orchestration.pipelines.runner import PipelineRunner
from agentic_os.kernel.world.events import EventLog


@pytest.fixture()
def runner(monkeypatch, tmp_path: Path):
    """PipelineRunner con DEV_ALLOW_ALL (tenants efímeros de test) y datos en tmp_path."""
    monkeypatch.setenv("DEV_ALLOW_ALL", "true")

    # Redirigir las raíces de datos de las tools hacia tmp_path para no ensuciar el repo
    import agentic_os.execution.tools.drive_tool as drive_mod
    import agentic_os.execution.tools.gmail_tool as gmail_mod

    monkeypatch.setattr(drive_mod, "_DATA_ROOT", tmp_path)
    monkeypatch.setattr(gmail_mod, "_DATA_ROOT", tmp_path)

    log = EventLog()
    executor = Executor(
        registry=build_default_registry(),
        event_log=log,
    )
    return PipelineRunner(executor=executor, llm=None)


def _seed_drive(tmp_path: Path) -> None:
    """Escribe un CSV de leads en la cache local de Drive del tenant 't1'."""
    drive_dir = tmp_path / "tenants" / "t1" / "drive" / "leads" / "t1"
    drive_dir.mkdir(parents=True, exist_ok=True)
    (drive_dir / "leads_2026.csv").write_text(
        "name,email\nAna,ana@empresa.com\nLuis,luis@otra.com\n",
        encoding="utf-8",
    )


def test_pipeline_leads_to_draft_crea_drafts_y_eventos(runner, tmp_path: Path) -> None:
    _seed_drive(tmp_path)
    result = runner.run("leads_to_draft", "t1", {})
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


def test_pipeline_inbox_watcher_simulado(runner) -> None:
    result = runner.run("inbox_watcher", "t2", {})
    assert result["status"] == "OK"
    assert result["processed"] == 2
    assert result["drafts_created"] == 1  # solo el email clasificado como lead