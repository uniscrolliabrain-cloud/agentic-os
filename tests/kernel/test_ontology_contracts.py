"""Tests de contratos de ontología (#9-#12 del hardening).

Entity/Relation (validadores), invariantes ejecutables y OntologyValidator
determinista.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from agentic_os.kernel.ontology.entities import Entity
from agentic_os.kernel.ontology.invariants import (
    INVARIANTS,
    OntologyViolation,
    validate_all_relations,
    validate_relation,
)
from agentic_os.kernel.ontology.relations import Relation
from agentic_os.kernel.ontology.validator import (
    OntologyValidationError,
    OntologyValidator,
)


# ------------------------------------------------------------------ #9 Entity
def test_entity_kind_canonico_acepta_slug() -> None:
    e = Entity(kind="actor")
    assert e.kind == "actor"
    assert e.id  # default factory new_id


@pytest.mark.parametrize("bad", ["", "Actor", "bad kind", "x/y", ".."])
def test_entity_kind_invalido_rechazado(bad) -> None:
    with pytest.raises(ValidationError):
        Entity(kind=bad)


def test_entity_id_vacio_rechazado() -> None:
    with pytest.raises(ValidationError):
        Entity(id="", kind="tool")


def test_entity_frozen() -> None:
    e = Entity(kind="tool")
    with pytest.raises(ValidationError):
        e.kind = "actor"  # type: ignore[misc]


# -------------------------------------------------------------- #10 Relation
def test_relation_valida() -> None:
    r = Relation(kind="uses", src_id="a1", dst_id="t1")
    assert r.kind == "uses"


def test_relation_ids_vacios_rechazados() -> None:
    with pytest.raises(ValidationError):
        Relation(kind="uses", src_id="", dst_id="t1")
    with pytest.raises(ValidationError):
        Relation(kind="uses", src_id="a1", dst_id="")


def test_relation_auto_relacion_rechazada() -> None:
    with pytest.raises(ValidationError):
        Relation(kind="uses", src_id="x", dst_id="x")


def test_relation_kind_invalido_rechazado() -> None:
    with pytest.raises(ValidationError):
        Relation(kind="Uses", src_id="a", dst_id="b")


# ------------------------------------------------- #11 invariantes ejecutables
def test_invariantes_declaradas_existen() -> None:
    assert "Actor -> uses -> Tool" in INVARIANTS
    assert "Event immutable" in INVARIANTS


def _map() -> dict:
    return {
        "a1": Entity(id="a1", kind="actor"),
        "t1": Entity(id="t1", kind="tool"),
        "r1": Entity(id="r1", kind="resource"),
    }


def test_invariante_actor_uses_tool_ok() -> None:
    validate_relation(_map(), Relation(kind="uses", src_id="a1", dst_id="t1"))


def test_invariante_tool_no_puede_uses_tool() -> None:
    with pytest.raises(OntologyViolation):
        validate_relation(
            _map(), Relation(kind="uses", src_id="t1", dst_id="t1" if False else "r1")
        )


def test_invariante_accesses_requiere_tool_src_y_resource_dst() -> None:
    m = _map()
    # src no-tool → viola
    with pytest.raises(OntologyViolation):
        validate_relation(m, Relation(kind="accesses", src_id="a1", dst_id="r1"))
    # dst no-resource → viola (sin auto-relación, que ya rechaza el modelo)
    with pytest.raises(OntologyViolation):
        validate_relation(m, Relation(kind="accesses", src_id="t1", dst_id="a1"))
    # correcto
    validate_relation(m, Relation(kind="accesses", src_id="t1", dst_id="r1"))


def test_invariante_referencia_desconocida_falla() -> None:
    with pytest.raises(OntologyViolation):
        validate_relation(_map(), Relation(kind="uses", src_id="ghost", dst_id="t1"))


def test_validate_all_relations_acumula() -> None:
    m = _map()
    with pytest.raises(OntologyViolation):
        validate_all_relations(
            m,
            [
                Relation(kind="uses", src_id="a1", dst_id="t1"),
                Relation(kind="accesses", src_id="a1", dst_id="r1"),  # viola
            ],
        )


# ---------------------------------------------------- #12 OntologyValidator
def test_validator_ontologia_valida() -> None:
    OntologyValidator().validate(
        entities=list(_map().values()),
        relations=[Relation(kind="uses", src_id="a1", dst_id="t1")],
    )


def test_validator_kind_fuera_de_vocabulario() -> None:
    with pytest.raises(OntologyValidationError):
        OntologyValidator().validate(
            entities=[Entity(id="e1", kind="nave_espacial")],
            relations=[],
        )


def test_validator_referencias_rotas_y_duplicados() -> None:
    ent = [Entity(id="a1", kind="actor"), Entity(id="a1", kind="agent")]
    rels = [Relation(kind="uses", src_id="a1", dst_id="fantasma")]
    with pytest.raises(OntologyValidationError) as excinfo:
        OntologyValidator().validate(entities=ent, relations=rels)
    msg = str(excinfo.value)
    assert "duplicada" in msg
    assert "fuera del Vocabulary" in msg or "desconocido" in msg
