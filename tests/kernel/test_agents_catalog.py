"""C4c: 5 agentes, handoffs bidireccionales, integridad de catalogo."""
from __future__ import annotations

def test_hay_5_agentes():
    from agentic_os.cognition.agents.seed import build_catalog
    cat = build_catalog()
    ids = sorted(a.id for a in cat.list_agents())
    assert len(ids) == 5
    assert ids == [
        "communication_agent",
        "content_agent",
        "data_analysis_agent",
        "lead_generation_agent",
        "web_research_agent",
    ]


def test_handoffs_bidireccionales():
    from agentic_os.cognition.agents.seed import build_catalog
    cat = build_catalog()
    ids = {a.id for a in cat.list_agents()}
    for a in cat.list_agents():
        for h in a.handoffs:
            assert h in ids, f"{a.id} -> {h} no existe en el catalogo"


def test_microacciones_existen_en_catalogo():
    from agentic_os.cognition.agents.seed import build_catalog
    cat = build_catalog()
    ma_ids = {m.id for m in cat.list_microactions()}
    for a in cat.list_agents():
        for m in a.microactions:
            assert m in ma_ids, f"{a.id} declara microaccion inexistente: {m}"


def test_tools_existen_en_registry():
    from agentic_os.cognition.agents.seed import build_catalog
    from agentic_os.execution.tools import build_default_registry
    reg = build_default_registry()
    tools = set(reg.tools.keys())
    cat = build_catalog()
    for a in cat.list_agents():
        for t in a.tools:
            assert t in tools, f"{a.id} declara tool inexistente: {t}"

