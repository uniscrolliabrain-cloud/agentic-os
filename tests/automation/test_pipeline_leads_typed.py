"""A9 — los pipelines crean entidades tipadas en el WorldState (Bloque A).

A9.1: leads_to_draft crea un Lead por lead valido y falla (fail-closed)
por lead con email invalido, sin crear su draft.
A9.2: daily_social crea un BlogPost con el copy y NO publica si la
entidad no valida (status=VALIDATION_ERROR, meta_post_publish nunca).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from agentic_os.execution.executor import Executor
from agentic_os.execution.tools import build_default_registry
from agentic_os.execution.tools.drive_tool import DriveListFilesTool, DriveReadFileTool
from agentic_os.infrastructure.config.settings import settings
from agentic_os.kernel.ontology.domain_models import BlogPost, Lead
from agentic_os.kernel.world.events import EventLog
from agentic_os.kernel.world.replay import replay
from agentic_os.orchestration.pipelines.runner import PipelineRunner


@pytest.fixture()
def runner(monkeypatch, tmp_path: Path) -> PipelineRunner:
    """Mismo entorno determinista que tests/automation/test_pipelines.py."""
    monkeypatch.setenv("DEV_ALLOW_ALL", "true")
    monkeypatch.setattr(settings, "google_real", False)

    import agentic_os.execution.tools.drive_tool as drive_mod
    import agentic_os.execution.tools.gmail_tool as gmail_mod

    monkeypatch.setattr(drive_mod, "_DATA_ROOT", tmp_path)
    monkeypatch.setattr(gmail_mod, "_DATA_ROOT", tmp_path)

    reg = build_default_registry()
    reg.register(DriveListFilesTool())
    reg.register(DriveReadFileTool())
    log = EventLog()
    executor = Executor(registry=reg, event_log=log)
    return PipelineRunner(executor=executor, llm=None)


def _seed_leads(tmp_path: Path, csv_text: str) -> None:
    drive_dir = tmp_path / "tenants" / "t1" / "drive" / "leads" / "t1"
    drive_dir.mkdir(parents=True, exist_ok=True)
    (drive_dir / "leads_2026.csv").write_text(csv_text, encoding="utf-8")


# ------------------------------------------------------- A9.1 leads --------

def test_leads_to_draft_crea_leads_tipados_y_errores(runner, tmp_path: Path) -> None:
    _seed_leads(
        tmp_path,
        "name,email\nAna,ana@empresa.com\nLuis,luis@otra.com\nBad,bad-email\n",
    )

    result = runner.run("leads_to_draft", "t1", {})

    assert result["status"] == "OK"
    assert result["drafts_created"] == 2
    assert len(result["errors"]) == 1
    assert "bad-email" in result["errors"][0]

    # Las entidades tipadas quedan reconstruibles desde el EventLog
    state = replay(runner.executor.event_log)
    leads = [e for e in state.entities.values() if isinstance(e, Lead)]
    assert len(leads) == 2
    assert {lead.email for lead in leads} == {"ana@empresa.com", "luis@otra.com"}
    assert all(lead.tenant_id == "t1" for lead in leads)
    for lead in leads:
        assert state.entities[lead.id] is lead


def test_leads_email_invalido_no_genera_draft(runner, tmp_path: Path) -> None:
    _seed_leads(tmp_path, "name,email\nSolo-Malo,no-es-un-email\n")

    result = runner.run("leads_to_draft", "t1", {})

    assert result["status"] == "OK"
    assert result["drafts_created"] == 0
    assert len(result["errors"]) == 1
    state = replay(runner.executor.event_log)
    assert not [e for e in state.entities.values() if isinstance(e, Lead)]


# ---------------------------------------------------- A9.2 daily social ----

class _FakeRunner:
    """Runner falso que graba llamadas a tool() y emit_event()."""

    def __init__(self, files):
        self._files = files
        self.tool_calls: list[tuple[str, dict]] = []
        self.events: list[tuple[str, str, dict]] = []

    def tool(self, name, params, tenant_id, correlation_id=None, command_id=None):
        self.tool_calls.append((name, params))
        if name == "drive_list_files":
            return {"files": self._files}
        if name == "drive_read_file":
            return {"content": "contenido de prueba del post"}
        if name == "meta_post_publish":
            return {"status": "SIMULATED", "real_execution": False}
        raise AssertionError(f"tool inesperada: {name}")

    def emit_event(self, kind, entity_id, tenant_id, payload, correlation_id=None, command_id=None):
        self.events.append((kind, entity_id, payload))


def test_daily_social_crea_blogpost_tipado(monkeypatch, tmp_path: Path) -> None:
    import agentic_os.orchestration.pipelines.pipeline_daily_social as mod

    monkeypatch.setattr(mod, "_DATA_ROOT", tmp_path)
    fake = _FakeRunner(files=[{"name": "post.csv", "path": "post.csv"}])

    result = mod.run_daily_social(fake, "t1", {}, None)

    assert result["status"] == "OK"
    assert fake.events, "el pipeline debe emitir entity_created"
    kind, entity_id, payload = fake.events[0]
    assert kind == "entity_created"
    assert payload["kind"] == "content.blog_post"
    assert entity_id == payload["id"]
    assert payload["body"] == "contenido de prueba del post"
    assert fake.tool_calls[-1][0] == "meta_post_publish"


def test_daily_social_titulo_vacio_no_publica(monkeypatch, tmp_path: Path) -> None:
    import agentic_os.orchestration.pipelines.pipeline_daily_social as mod

    monkeypatch.setattr(mod, "_DATA_ROOT", tmp_path)
    # Un candidate con name vacio fuerza BlogPost(title="") -> ValidationError
    fake = _FakeRunner(files=[{"name": "", "path": "post.csv"}])

    result = mod.run_daily_social(fake, "t1", {}, None)

    assert result["status"] == "VALIDATION_ERROR"
    assert "title" in result["error"]
    assert not [n for n, _ in fake.tool_calls if n == "meta_post_publish"]
    assert fake.events == []
