"""FASE 1.5 - Auditoría infranqueable (fail-closed).

Si la auditoría obligatoria no puede persistirse, la operación NO puede
declararse exitosa. Cubre Executor.execute(), Scheduler._fire() y la carga
del AuditLog.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from agentic_os.connectors.core.audit import AuditLog
from agentic_os.execution.executor import Executor
from agentic_os.execution.tools import ToolRegistry
from agentic_os.orchestration.scheduler import Scheduler


class FakeTool:
    def __init__(self) -> None:
        self.name = "fake_success"
        self.calls = 0

    def run(self, params: dict) -> dict:
        self.calls += 1
        return {"ok": True, "calls": self.calls}


class OkLog:
    def __init__(self) -> None:
        self.events: list[Any] = []

    def append(self, event: Any) -> None:
        self.events.append(event)


class AlwaysFailLog:
    def append(self, event: Any) -> None:
        raise OSError("disk full (simulado)")


class FailOnToolCompletedLog:
    def __init__(self) -> None:
        self.events: list[Any] = []
        self.fail_on_kind = "ToolCompleted"

    def append(self, event: Any) -> None:
        if event.kind == self.fail_on_kind:
            raise OSError(f"append falló para {event.kind} (simulado)")
        self.events.append(event)


def _executor(log: Any) -> tuple[Executor, FakeTool]:
    reg = ToolRegistry()
    tool = FakeTool()
    reg.register(tool)
    return Executor(registry=reg, event_log=log), tool


def test_eventlog_ok_ejecucion_normal(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEV_ALLOW_ALL", "true")
    ex, tool = _executor(OkLog())
    result = ex.execute("fake_success", {"x": 1}, tenant_id="t-ok")
    assert result["success"] is True
    assert tool.calls == 1


def test_eventlog_falla_ejecucion_abortada(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEV_ALLOW_ALL", "true")
    ex, tool = _executor(AlwaysFailLog())
    result = ex.execute("fake_success", {"x": 1}, tenant_id="t-abort")
    assert result["success"] is False
    assert tool.calls == 0, "la tool no debe ejecutarse si la auditoría inicial falló"
    assert "disk full" in result["error"]


def test_eventlog_falla_despues_del_efecto_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DEV_ALLOW_ALL", "true")
    ex, tool = _executor(FailOnToolCompletedLog())
    result = ex.execute("fake_success", {"x": 1}, tenant_id="t-effect")
    assert tool.calls == 1, "el efecto se preparó/produjo"
    assert result["success"] is False, "fail-closed: no se declara éxito sin auditoría"


def test_error_de_persistencia_observable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEV_ALLOW_ALL", "true")
    ex, _ = _executor(AlwaysFailLog())
    result = ex.execute("fake_success", {"x": 1}, tenant_id="t-observable")
    assert result["success"] is False
    assert result["error"] and "disk full" in result["error"]


def test_scheduler_audita_fallo_de_pipeline(tmp_path: Path) -> None:
    log = OkLog()
    scheduler = Scheduler(data_dir=tmp_path, event_log=log)

    def bad_trigger(pipeline_id, tenant_id, correlation_id=None, command_id=None) -> None:
        raise RuntimeError("pipeline boom")

    scheduler.on_trigger = bad_trigger
    # El fallo del trigger se audita (ScheduledPipelineFailed) y no se propaga
    # porque la auditoría del fallo sí se puede persistir.
    scheduler._fire("t-aud", "daily_social", "sched-1")
    kinds = [e.kind for e in log.events]
    assert "ScheduledPipelineFailed" in kinds


def test_scheduler_no_se_traga_fallo_de_auditoria(tmp_path: Path) -> None:
    scheduler = Scheduler(data_dir=tmp_path, event_log=AlwaysFailLog())

    def bad_trigger(pipeline_id, tenant_id, correlation_id=None, command_id=None) -> None:
        raise RuntimeError("pipeline boom")

    scheduler.on_trigger = bad_trigger
    with pytest.raises(Exception) as excinfo:
        scheduler._fire("t-noaudit", "daily_social", "sched-2")
    assert excinfo.value is not None


def test_auditlog_linea_corrupta_observable(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    p = tmp_path / "audit.jsonl"
    p.write_text(
        '{"audit_id":"1","capability":"a","operation":"x","status":"ok","timestamp":"2026-09-08T00:00:00Z"}\n'
        "not-json-line\n",
        encoding="utf-8",
    )
    import logging

    with caplog.at_level(logging.WARNING):
        log = AuditLog(log_path=str(p))
    assert len(log.all()) == 1
    assert any("corrupta" in r.getMessage() for r in caplog.records)