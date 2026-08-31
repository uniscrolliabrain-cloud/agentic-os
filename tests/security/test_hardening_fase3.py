"""FASE 3 — EventLog una sola fuente de verdad + auditoría real del Executor.

Criterios de aceptación:
1. Orchestrator.tick() funciona igual con EventLog in-memory y JsonlEventLog.
2. Ejecutar una acción exitosa deja ActionStarted + ToolCompleted en el log.
3. GmailSendTool sin to/subject -> Executor.execute() success=False (no True).
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from src.agentic_os.execution.executor import Executor
from src.agentic_os.execution.tools import ToolRegistry
from src.agentic_os.execution.tools.gmail_tool import GmailSendTool
from src.agentic_os.execution.tools.base import ToolValidationError
from src.agentic_os.infrastructure.persistence.jsonl import JsonlEventLog
from src.agentic_os.kernel.policy.engine import PolicyEngine
from src.agentic_os.kernel.world.events import Event, EventLog
from src.agentic_os.orchestration.orchestrator import Orchestrator
from src.agentic_os.interfaces.llm.provider import MockLLMProvider


# ----------------------------------------------------- 1. tick agnóstico --
def test_tick_funciona_con_eventlog_inmemory():
    log = EventLog()
    log.append(Event(kind="IntentProposed", entity_id="e1", tenant_id="t1"))
    orch = Orchestrator(log=log, llm=MockLLMProvider())
    result = orch.tick()
    assert result["state"] is not None
    assert result["role"]


def test_tick_funciona_con_jsonleventlog(tmp_path: Path):
    """Bugfix 3.1: antes tick()/replay() leían `.events`, atributo que no
    existe en JsonlEventLog -> AttributeError en runtime."""
    log = JsonlEventLog(base_dir=tmp_path / "ev")
    log.append(Event(kind="IntentProposed", entity_id="e1", tenant_id="t1"))
    log.append(Event(kind="IntentProposed", entity_id="e2", tenant_id="t2"))
    orch = Orchestrator(log=log, llm=MockLLMProvider())
    result = orch.tick()  # no debe lanzar AttributeError
    assert result["state"] is not None


# ------------------------------------------- 2. auditoría del Executor --
def test_ejecucion_exitosa_deja_eventos_de_auditoria(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    # Camino "permitido": el allow-all SOLO se activa con el flag explícito
    # (FASE 1: ENV=dev por sí solo no concede nada).
    monkeypatch.setenv("DEV_ALLOW_ALL", "true")
    log = JsonlEventLog(base_dir=tmp_path / "ev")
    # Registry con el mock explícito: este test audita el CICLO del Executor,
    # no la resolución (la resolución unificada gmail_send->kernel la cubre
    # tests/connectors/test_unified_execution.py).
    reg = ToolRegistry()
    reg.register(GmailSendTool())
    ex = Executor(registry=reg, policy_engine=PolicyEngine(), event_log=log)
    res = ex.execute("gmail_send", {"to": "a@b.com", "subject": "hola", "body": "x"},
                     context=None, tenant_id="t-audit")
    assert res["success"] is True
    kinds = [e.kind for e in log.list_for_tenant("t-audit")]
    assert "ActionStarted" in kinds
    assert "ToolCompleted" in kinds


def test_denegacion_deja_evento_action_denied(tmp_path: Path):
    log = JsonlEventLog(base_dir=tmp_path / "ev")
    engine = PolicyEngine()
    ex = Executor(registry=None, policy_engine=engine, event_log=log)
    # capability que la default policy deniega (p.ej. no registrada -> deny
    # no está garantizado; probamos con la ruta de 'tool no encontrada')
    res = ex.execute("capability_inexistente_xyz", {}, context=None, tenant_id="t-x")
    assert res["success"] is False
    kinds = [e.kind for e in log.list_for_tenant("t-x")]
    assert "ToolFailed" in kinds or "ActionDenied" in kinds


# --------------------------------------- 3. contrato de errores de tools --
def test_gmail_sin_campos_obligatorios_da_success_false(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Bugfix 3.3: antes la tool devolvía {"error": ...} y el Executor lo
    envolvía como success=True. Ahora lanza ToolValidationError."""
    # Permitimos la capability con el flag explícito para llegar HASTA la tool
    # y demostrar que el fallo de validación se propaga como success=False.
    monkeypatch.setenv("DEV_ALLOW_ALL", "true")
    log = JsonlEventLog(base_dir=tmp_path / "ev")
    # Mock explícito: la tool real (bridge) fallaría antes por credenciales.
    reg = ToolRegistry()
    reg.register(GmailSendTool())
    ex = Executor(registry=reg, policy_engine=PolicyEngine(), event_log=log)
    res = ex.execute("gmail_send", {"body": "sin to ni subject"},
                     context=None, tenant_id="t-err")
    assert res["success"] is False
    assert "obligatorios" in res["error"]
    kinds = [e.kind for e in log.list_for_tenant("t-err")]
    assert "ToolFailed" in kinds


def test_tool_lanza_excepcion_tipada():
    with pytest.raises(ToolValidationError):
        GmailSendTool().run({})


def test_todas_las_tools_validan_con_excepcion():
    from src.agentic_os.execution.tools.slack_tool import SlackSendTool
    from src.agentic_os.execution.tools.whatsapp_tool import WhatsAppSendTool
    from src.agentic_os.execution.tools.calendar_tool import CalendarCreateEventTool
    from src.agentic_os.execution.tools.scraper_tool import WebScrapeTool, WebSearchTool

    with pytest.raises(ToolValidationError):
        SlackSendTool().run({})
    with pytest.raises(ToolValidationError):
        WhatsAppSendTool().run({})
    with pytest.raises(ToolValidationError):
        CalendarCreateEventTool().run({})
    with pytest.raises(ToolValidationError):
        WebScrapeTool().run({})
    with pytest.raises(ToolValidationError):
        WebSearchTool().run({})


def test_ninguna_tool_devuelve_dict_con_clave_error():
    """Cinturón y tirantes: ninguna salida de tool mock contiene 'error'."""
    tools = [
        (GmailSendTool(), {"to": "a@b.com", "subject": "s", "body": "b"}),
    ]
    for tool, params in tools:
        out = tool.run(params)
        assert "error" not in out, f"{tool.name} sigue devolviendo clave 'error'"
