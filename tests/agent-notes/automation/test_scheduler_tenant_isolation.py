"""FASE 6: aislamiento por tenant del Scheduler y de los schedules persistidos."""

from __future__ import annotations

from pathlib import Path

from agentic_os.orchestration.scheduler import Scheduler


def _make_scheduler(tmp_path: Path) -> Scheduler:
    return Scheduler(data_dir=tmp_path)


def test_schedules_aislados_por_tenant(tmp_path: Path) -> None:
    sch = _make_scheduler(tmp_path)
    a = sch.schedule_interval("tenant-a", "inbox_watcher", minutes=30)
    b = sch.schedule_daily("tenant-b", "daily_social", hour=9)

    # cada tenant solo ve los suyos
    assert sch.list_schedules("tenant-a") == [a]
    assert sch.list_schedules("tenant-b") == [b]

    # borrar uno del tenant-b no afecta al tenant-a
    sch.remove_schedule("tenant-b", b["id"])
    assert sch.list_schedules("tenant-a") == [a]
    assert sch.list_schedules("tenant-b") == []


def test_schedules_persistidos_por_tenant(tmp_path: Path) -> None:
    sch = _make_scheduler(tmp_path)
    sch.schedule_interval("tenant-x", "inbox_watcher", minutes=15)
    sch.schedule_daily("tenant-y", "daily_social", hour=8)

    # la persistencia vive en data/tenants/<tenant>/schedules.json
    file_x = tmp_path / "tenants" / "tenant-x" / "schedules.json"
    file_y = tmp_path / "tenants" / "tenant-y" / "schedules.json"
    assert file_x.exists()
    assert file_y.exists()
    assert "tenant-x" in file_x.read_text(encoding="utf-8")
    assert "tenant-x" not in file_y.read_text(encoding="utf-8")


def test_remove_schedule_inexistente_no_rompe(tmp_path: Path) -> None:
    sch = _make_scheduler(tmp_path)
    assert sch.remove_schedule("tenant-z", "no-existe") is False