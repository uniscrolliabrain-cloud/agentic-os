"""C1e: E2E Intent -> Policy -> Executor -> Tool stub -> EventLog."""
from __future__ import annotations

import pytest

from agentic_os.execution.executor import Executor
from agentic_os.execution.tools.base import Tool
from agentic_os.execution.tools.registry import ToolRegistry
from agentic_os.infrastructure.persistence.memory import MemoryEventLog
from agentic_os.kernel.policy.engine import PolicyEngine


class EchoTool(Tool):
    name = "echo_stub"

    def run(self, params):
        return {"echo": params.get("msg", "")}


class DeleteThingTool(Tool):
    name = "thing.delete"

    def run(self, params):
        return {"deleted": True}


def _executor():
    reg = ToolRegistry()
    reg.register(EchoTool())
    reg.register(DeleteThingTool())
    log = MemoryEventLog()
    return Executor(registry=reg, policy_engine=PolicyEngine(), event_log=log), log


def test_deny_tenant_desconocido(monkeypatch):
    monkeypatch.delenv("DEV_ALLOW_ALL", raising=False)
    ex, log = _executor()
    res = ex.execute("echo_stub", {"msg": "hi"}, tenant_id="tenant-fantasma")
    assert res["success"] is False
    kinds = [e.kind for e in log.list_for_tenant("tenant-fantasma")]
    assert "ActionDenied" in kinds


def test_deny_sin_tenant(monkeypatch):
    monkeypatch.delenv("DEV_ALLOW_ALL", raising=False)
    ex, log = _executor()
    res = ex.execute("echo_stub", {"msg": "hi"})
    assert res["success"] is False
    assert "deny" in (res.get("error") or "").lower() or "tenant" in (res.get("error") or "").lower()


def test_allow_con_dev_allow_all(monkeypatch):
    monkeypatch.setenv("DEV_ALLOW_ALL", "true")
    ex, log = _executor()
    res = ex.execute("echo_stub", {"msg": "hola"}, tenant_id="t-dev")
    assert res["success"] is True
    assert res["output"]["echo"] == "hola"
    kinds = [e.kind for e in log.list_for_tenant("t-dev")]
    assert "ActionStarted" in kinds
    assert "ToolCompleted" in kinds


def test_needs_approval_por_invariante_delete(monkeypatch):
    monkeypatch.setenv("DEV_ALLOW_ALL", "true")
    ex, log = _executor()
    res = ex.execute("thing.delete", {"id": "x"}, tenant_id="t-del")
    assert res["success"] is False
    assert res["error"] == "approval required"
    kinds = [e.kind for e in log.list_for_tenant("t-del")]
    assert "ApprovalRequired" in kinds


def test_tool_inexistente_falla_limpio(monkeypatch):
    monkeypatch.setenv("DEV_ALLOW_ALL", "true")
    ex, log = _executor()
    res = ex.execute("no_existe", {}, tenant_id="t-x")
    assert res["success"] is False
    assert "no encontrada" in (res.get("error") or "")
    kinds = [e.kind for e in log.list_for_tenant("t-x")]
    assert "ToolFailed" in kinds


def test_correlation_y_command_se_propagan(monkeypatch):
    monkeypatch.setenv("DEV_ALLOW_ALL", "true")
    ex, log = _executor()
    res = ex.execute("echo_stub", {"msg": "x"}, tenant_id="t-c",
                     correlation_id="corr-1", command_id="cmd-1")
    assert res["success"] is True
    for e in log.list_for_tenant("t-c"):
        assert e.correlation_id == "corr-1"
        assert e.command_id == "cmd-1"

