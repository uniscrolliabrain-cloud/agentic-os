"""Spec 10 §02 LEAD_GENERATION_AGENT: contrato minimo."""
from __future__ import annotations


def test_agente_existe(catalog):
    a = catalog.agent("lead_generation_agent")
    assert a is not None
    assert a.name == "LEAD_GENERATION_AGENT"


def test_handoffs_a_web_research_y_communication(catalog):
    a = catalog.agent("lead_generation_agent")
    assert "web_research_agent" in a.handoffs
    assert "communication_agent" in a.handoffs


def test_microacciones_declaradas_existen(catalog):
    a = catalog.agent("lead_generation_agent")
    ma_ids = {m.id for m in catalog.list_microactions()}
    for m in a.microactions:
        assert m in ma_ids


def test_tools_declaradas_existen(catalog):
    from agentic_os.execution.tools import build_default_registry
    reg = build_default_registry()
    tools = set(reg.tools.keys())
    a = catalog.agent("lead_generation_agent")
    for t in a.tools:
        assert t in tools

