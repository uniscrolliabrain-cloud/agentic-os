"""Tests FASE 1.3 — Entity/Relation del kernel/ontology, estrictos y tipados."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from agentic_os.kernel.ontology import (
    DEFAULT_VOCAB,
    Entity,
    OntologyValidator,
    Relation,
)
from agentic_os.kernel.ontology.domain_models import DomainEntity, EntityRef


def _entity(kind: str, entity_id: str) -> Entity:
    return Entity(
        ref=EntityRef(entity_id=entity_id, entity_type=kind, tenant_id="t"),
        data=DomainEntity(entity_type=kind, tenant_id="t"),
    )


def test_entity_rechaza_campos_extra() -> None:
    with pytest.raises(ValidationError):
        _entity("actor", "a1").data.model_validate(
            {"entity_type": "actor", "tenant_id": "t", "campo_extra": "x"}
        )


def test_entity_rechaza_atributos_con_clave_no_str() -> None:
    with pytest.raises(ValidationError):
        _entity("actor", "a1").data.model_validate(
            {"entity_type": "actor", "tenant_id": 1}
        )


def test_relation_rechaza_auto_relacion() -> None:
    with pytest.raises(ValidationError):
        Relation(kind="uses", src_id="e-1", dst_id="e-1")


def test_relation_rechaza_kind_slug_invalido() -> None:
    with pytest.raises(ValidationError):
        Relation(kind="Uses Tool", src_id="e-1", dst_id="e-2")


def test_modelos_inmutables() -> None:
    entity = _entity("actor", "e-1")
    relation = Relation(kind="uses", src_id="e-1", dst_id="e-2")
    with pytest.raises(ValidationError):
        entity.kind = "tool"
    with pytest.raises(ValidationError):
        relation.kind = "accesses"


def test_validator_rechaza_kind_fuera_de_vocabulario() -> None:
    validator = OntologyValidator(DEFAULT_VOCAB)
    assert validator.validate_entity(_entity("actor", "e-1")) is True
    assert validator.validate_entity(_entity("nave_espacial", "e-1")) is False
    assert (
        validator.validate_relation(
            Relation(kind="warp", src_id="a", dst_id="b")
        )
    ) is False