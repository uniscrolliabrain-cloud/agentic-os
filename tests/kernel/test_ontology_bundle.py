"""Tests FASE 1.3b - Vocabulary extensible + OntologyBundle fail-closed."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from agentic_os.kernel.ontology import (
    DEFAULT_VOCAB,
    OntologyBundle,
    OntologyValidationError,
    is_canonical_kind,
    validate_against_metamodel,
)
from agentic_os.kernel.ontology.domain_models import DomainEntity, EntityRef
from agentic_os.kernel.ontology.entities import Entity
from agentic_os.kernel.ontology.relations import Relation
from agentic_os.kernel.ontology.validator import OntologyValidator
from agentic_os.domains.base import BaseDomain


class ClinicDomain(BaseDomain):
    domain = "clinic"
    entity_kinds = {"clinic.patient", "clinic.appointment"}
    relation_kinds = {"clinic.has_appointment"}
    capability_kinds = {"clinic.schedule"}


@pytest.mark.parametrize(
    "kind",
    ["actor", "user", "tool", "clinic.patient", "marketing.lead",
     "belongs_to", "has_appointment", "e-1", "sales.lead.created"],
)
def test_is_canonical_kind_valid(kind: str) -> None:
    assert is_canonical_kind(kind) is True


@pytest.mark.parametrize(
    "kind",
    ["Actor", "bad kind", "x/y", "..", "", "CamelCase", "UPPER",
     "1abc", "a..b", "a-"],
)
def test_is_canonical_kind_invalid(kind: str) -> None:
    assert is_canonical_kind(kind) is False


def test_validate_valid_domain_produces_bundle() -> None:
    bundle = validate_against_metamodel(
        entity_kinds={"clinic.patient"},
        relation_kinds={"clinic.has_appointment"},
        capability_kinds={"clinic.schedule"},
        tenant_scope="tenant_clinic",
    )
    assert isinstance(bundle, OntologyBundle)
    assert bundle.tenant_scope == "tenant_clinic"
    assert bundle.frozen is True
    assert "clinic.patient" in bundle.entities
    assert "clinic.has_appointment" in bundle.relations
    assert "clinic.schedule" in bundle.capabilities
    assert DEFAULT_VOCAB.entities <= set(bundle.entities)


def test_rejects_non_canonical_kind() -> None:
    with pytest.raises(OntologyValidationError, match="no can"):
        validate_against_metamodel(entity_kinds={"Patient"})


def test_rejects_default_vocab_collision() -> None:
    with pytest.raises(OntologyValidationError, match="colisi"):
        validate_against_metamodel(entity_kinds={"actor"})


def test_rejects_relation_referencing_undeclared_entity() -> None:
    ent = _make_entity("clinic.patient", "p1")
    rel = Relation(kind="uses", src_id="ghost", dst_id="p1")
    with pytest.raises(OntologyValidationError, match="src_id no declarado"):
        validate_against_metamodel(
            entity_kinds={"clinic.patient"},
            entities=[ent],
            relations=[rel],
            tenant_scope="t",
        )


def test_bundle_is_frozen_and_versioned() -> None:
    bundle = validate_against_metamodel(
        entity_kinds={"clinic.patient"},
        tenant_scope="t",
    )
    assert bundle.version == 1
    assert bundle.frozen is True
    with pytest.raises(ValidationError):
        bundle.tenant_scope = "otro"


def test_bundle_vocabulary_property() -> None:
    bundle = validate_against_metamodel(
        entity_kinds={"clinic.patient"},
        relation_kinds={"clinic.has_appointment"},
        capability_kinds={"clinic.schedule"},
        tenant_scope="clinic",
    )
    vocab = bundle.vocabulary
    assert isinstance(vocab, type(DEFAULT_VOCAB))
    assert "clinic.patient" in vocab.entities
    assert "actor" in vocab.entities


def test_bundle_extended_properties() -> None:
    bundle = validate_against_metamodel(
        entity_kinds={"clinic.patient", "clinic.appointment"},
        relation_kinds={"clinic.has_appointment"},
        capability_kinds={"clinic.schedule"},
        tenant_scope="clinic",
    )
    assert bundle.extended_entities == {"clinic.patient", "clinic.appointment"}
    assert bundle.extended_relations == {"clinic.has_appointment"}
    assert bundle.extended_capabilities == {"clinic.schedule"}


def test_validator_from_bundle_accepts_domain_entity() -> None:
    bundle = validate_against_metamodel(
        entity_kinds={"clinic.patient"},
        tenant_scope="clinic",
    )
    validator = OntologyValidator.from_bundle(bundle)
    ent = _make_entity("clinic.patient", "p1")
    assert validator.validate_entity(ent) is True
    alien = _make_entity("finance.invoice", "f1")
    assert validator.validate_entity(alien) is False


def test_clinic_compiles_ontology() -> None:
    bundle = ClinicDomain.compile_ontology()
    assert isinstance(bundle, OntologyBundle)
    assert bundle.tenant_scope == "clinic"
    assert "clinic.patient" in bundle.entities
    assert "clinic.appointment" in bundle.entities
    assert "clinic.has_appointment" in bundle.relations
    assert "clinic.schedule" in bundle.capabilities


def test_clinic_default_vocab_intact() -> None:
    original = set(DEFAULT_VOCAB.entities)
    ClinicDomain.compile_ontology()
    assert set(DEFAULT_VOCAB.entities) == original


def test_clinic_get_extended_vocab() -> None:
    vocab = ClinicDomain.get_extended_vocab()
    assert DEFAULT_VOCAB.entities <= vocab.entities
    assert "clinic.patient" in vocab.entities
    assert "clinic.has_appointment" in vocab.relations


def test_base_domain_empty_compiles_to_default() -> None:
    bundle = BaseDomain.compile_ontology(tenant_override="default")
    assert bundle.tenant_scope == "default"
    assert set(bundle.relations) == set(DEFAULT_VOCAB.relations)
    assert set(bundle.capabilities) == set(DEFAULT_VOCAB.capabilities)


def _make_entity(kind: str, entity_id: str) -> Entity:
    return Entity(
        ref=EntityRef(entity_id=entity_id, entity_type=kind, tenant_id="t"),
        data=DomainEntity(entity_type=kind, tenant_id="t"),
    )