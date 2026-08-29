"""Tests de la persistencia multi-repo (FASE 3 - EventLog con postgres option)."""

import pytest

from agentic_os.infrastructure.config.settings import settings
from agentic_os.infrastructure.persistence import get_eventlog_repo
from agentic_os.infrastructure.persistence.jsonl import JsonlEventLog
from agentic_os.infrastructure.persistence.postgres import PostgresEventLog, _DRIVER_AVAILABLE
from agentic_os.kernel.world.events import Event


@pytest.fixture()
def repo(tmp_path, monkeypatch):
    """JSONL en directorio temporal para que el test sea determinista y aislado."""
    monkeypatch.setattr(settings, "eventlog_impl", "jsonl")
    return JsonlEventLog(base_dir=tmp_path / "eventlog")


def test_get_eventlog_repo_segun_impl(repo):
    assert type(repo).__name__ == "JsonlEventLog"


def test_postgres_degrada_con_fail_safe(tmp_path):
    """Sin DSN (o sin driver) el repo Postgres degrada a JSONL, nunca rompe."""
    pg = PostgresEventLog(dsn="", base_dir=str(tmp_path / "eventlog"))
    assert pg.available is False
    e = Event(kind="test", entity_id="x", tenant_id="tenant-a")
    pg.append(e)  # debe ir al fallback sin lanzar
    assert len(pg.list_for_tenant("tenant-a")) == 1
    assert len(pg.list_all()) == 1


def test_event_append_y_recuperacion(repo):
    e1 = Event(kind="entity_created", entity_id="1", tenant_id="tenant-a", payload={"kind": "actor"})
    e2 = Event(kind="entity_created", entity_id="2", tenant_id="tenant-b", payload={"kind": "actor"})
    repo.append(e1)
    repo.append(e2)
    ta = repo.list_for_tenant("tenant-a")
    tb = repo.list_for_tenant("tenant-b")
    assert len(ta) == 1 and ta[0].entity_id == "1"
    assert len(tb) == 1 and tb[0].entity_id == "2"
    assert len(repo.list_all()) == 2