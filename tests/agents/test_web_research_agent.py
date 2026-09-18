"""Spec 10 §01 WEB_RESEARCH_AGENT: contrato minimo."""
from __future__ import annotations


def test_agente_existe(catalog):
    a = catalog.agent("web_research_agent")
    assert a is not None
    assert a.name == "WEB_RESEARCH_AGENT"


def test_microacciones_declaradas_existen(catalog):
    a = catalog.agent("web_research_agent")
    ma_ids = {m.id for m in catalog.list_microactions()}
    for m in a.microactions:
        assert m in ma_ids


def test_tools_declaradas_existen(catalog):
    from agentic_os.execution.tools import build_default_registry
    reg = build_default_registry()
    tools = set(reg.tools.keys())
    a = catalog.agent("web_research_agent")
    for t in a.tools:
        assert t in tools


def test_handoffs_resuelven(catalog):
    ids = {x.id for x in catalog.list_agents()}
    a = catalog.agent("web_research_agent")
    for h in a.handoffs:
        assert h in ids

