"""Tests C2c/C2d/C2e: taxonomy, schema extendido, integridad."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from agentic_os.cognition.agents.schemas import MicroActionSchema
from agentic_os.kernel.ontology.taxonomy import (
    ALL_FAMILIES,
    FUTURE_FAMILIES,
    is_valid_taxonomy,
)


def _ma(**kw):
    base = {
        "id": "web.test",
        "action_type": "Read",
        "entity_type": "URL",
        "taxonomy": "WEB",
        "purpose": "test",
        "tool": "fake_tool",
    }
    base.update(kw)
    return MicroActionSchema(**base)


def test_15_familias():
    assert len(ALL_FAMILIES) == 15


def test_16_futuras():
    assert len(FUTURE_FAMILIES) == 16


def test_is_valid_taxonomy():
    assert is_valid_taxonomy("WEB") is True
    assert is_valid_taxonomy("INVENTADA") is False
    assert is_valid_taxonomy("") is False


def test_ma_con_taxonomy_invalida_falla():
    with pytest.raises(ValidationError, match="taxonomy invalida"):
        _ma(taxonomy="INVENTADA")


def test_ma_con_action_type_invalido_falla():
    with pytest.raises(ValidationError, match="action_type invalido"):
        _ma(action_type="Destroy")


def test_ma_con_par_prohibido_falla():
    with pytest.raises(ValidationError, match="par prohibido"):
        _ma(action_type="Delete", entity_type="Person")


def test_ma_valida_pasa():
    ma = _ma()
    assert ma.stub is False
    assert ma.taxonomy == "WEB"


def test_stub_default_false():
    assert _ma().stub is False


def test_stub_true_si_se_pide():
    assert _ma(stub=True).stub is True


def test_todos_los_pipelines_apuntan_a_microacciones_existentes():
    """C2e: los pipelines del catalogo no referencian microacciones huerfanas.

    Carga el catalogo seedeado y verifica que todo microaction_id de
    un PipelineStep existe en el catalogo de microacciones.
    """
    from agentic_os.cognition.agents.seed import build_catalog

    cat = build_catalog()
    known = {ma.id for ma in cat.list_microactions()}
    for p in cat.list_pipelines():
        for step in p.steps:
            assert step.microaction_id in known, (
                f"pipeline {p.id!r} referencia microaccion inexistente: {step.microaction_id!r}"
            )


def test_ningun_agente_del_catalogo_apunta_a_agente_inexistente():
    """Los handoffs declarados deben existir en el catalogo."""
    from agentic_os.cognition.agents.seed import build_catalog

    cat = build_catalog()
    agent_ids = {a.id for a in cat.list_agents()}
    for a in cat.list_agents():
        for h in a.handoffs:
            assert h in agent_ids, (
                f"agente {a.id!r} declara handoff a inexistente: {h!r}"
            )

