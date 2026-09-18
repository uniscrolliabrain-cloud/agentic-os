"""Spec 10 §05 CONTENT_AGENT: contrato minimo."""
from __future__ import annotations


def test_agente_existe(catalog):
    a = catalog.agent("content_agent")
    assert a is not None
    assert a.name == "CONTENT_AGENT"


def test_handoff_a_communication(catalog):
    a = catalog.agent("content_agent")
    assert "communication_agent" in a.handoffs


def test_microacciones_declaradas_existen(catalog):
    a = catalog.agent("content_agent")
    ma_ids = {m.id for m in catalog.list_microactions()}
    for m in a.microactions:
        assert m in ma_ids


def test_tools_declaradas_existen(catalog):
    from agentic_os.execution.tools import build_default_registry
    reg = build_default_registry()
    tools = set(reg.tools.keys())
    a = catalog.agent("content_agent")
    for t in a.tools:
        assert t in tools

