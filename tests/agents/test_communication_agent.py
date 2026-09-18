"""Spec 10 §03 COMMUNICATION_AGENT: contrato minimo."""
from __future__ import annotations


def test_agente_existe(catalog):
    a = catalog.agent("communication_agent")
    assert a is not None
    assert a.name == "COMMUNICATION_AGENT"


def test_microacciones_declaradas_existen(catalog):
    a = catalog.agent("communication_agent")
    ma_ids = {m.id for m in catalog.list_microactions()}
    for m in a.microactions:
        assert m in ma_ids


def test_tools_declaradas_existen(catalog):
    from agentic_os.execution.tools import build_default_registry
    reg = build_default_registry()
    tools = set(reg.tools.keys())
    a = catalog.agent("communication_agent")
    for t in a.tools:
        assert t in tools


def test_human_approval_required(catalog):
    a = catalog.agent("communication_agent")
    assert a.human_approval_policy.get("required") is True

