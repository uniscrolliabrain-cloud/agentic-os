from __future__ import annotations

from typing import Any, Iterable, Set

from ..kernel.ontology import DEFAULT_VOCAB, Vocabulary, OntologyBundle
from ..kernel.ontology.validator import validate_against_metamodel
from ..kernel.ontology.entities import Entity
from ..kernel.ontology.relations import Relation


class BaseDomain:
    """Base para dominios/nicho.

    **Regla de oro**: el kernel define qué *PUEDE* existir
    (``DEFAULT_VOCAB``); el dominio define qué *EXISTE* mediante
    extensiones tipadas.  ``compile_ontology()`` valida fail-closed
    contra el metamodelo y produce un ``OntologyBundle`` versionado.
    """

    domain: str = ""
    entity_kinds: Set[str] = set()
    relation_kinds: Set[str] = set()
    capability_kinds: Set[str] = set()

    @classmethod
    def get_extended_vocab(cls) -> Vocabulary:
        """Vocabulary canónico: DEFAULT_VOCAB + extensiones del dominio."""
        return Vocabulary(
            entities=DEFAULT_VOCAB.entities | cls.entity_kinds,
            relations=DEFAULT_VOCAB.relations | cls.relation_kinds,
            capabilities=DEFAULT_VOCAB.capabilities | cls.capability_kinds,
        )

    @classmethod
    def compile_ontology(
        cls,
        *,
        entities: Iterable[Entity[Any]] = (),
        relations: Iterable[Relation] = (),
        default_vocab: Vocabulary = DEFAULT_VOCAB,
        tenant_override: str | None = None,
    ) -> OntologyBundle:
        """Valida fail-closed la ontología del dominio y produce OntologyBundle.

        Entry point del kernel:
        ``tenant → declara ontología → kernel valida → acepta/rechaza``.
        Nunca un LLM registra un esquema directamente en runtime.
        """
        return validate_against_metamodel(
            entity_kinds=cls.entity_kinds,
            relation_kinds=cls.relation_kinds,
            capability_kinds=cls.capability_kinds,
            entities=entities,
            relations=relations,
            tenant_scope=tenant_override or cls.domain,
            default_vocab=default_vocab,
        )
