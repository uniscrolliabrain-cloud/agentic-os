from __future__ import annotations

from typing import Set

from ..types import KernelModel
from .metamodel import EntityMeta, RelationMeta, CapabilityMeta
from .entities import Entity
from .relations import Relation
from .capabilities import Capability
from .vocabulary import Vocabulary, DEFAULT_VOCAB, is_canonical_kind
from .validator import OntologyValidator, OntologyValidationError, validate_against_metamodel


class OntologyBundle(KernelModel):
    """Foto auditable, congelada y versionada de la ontología efectiva de un tenant.

    El kernel valida fail-closed las declaraciones del dominio
    (``validate_against_metamodel``) y produce un ``OntologyBundle``
    congelado.  Cada tenant obtiene una *foto* inmutable, nunca un dict
    mutable, lo que permite auditoría y replay determinista.
    """

    version: int = 1
    tenant_scope: str = ""
    entities: Set[str]
    relations: Set[str]
    capabilities: Set[str]
    frozen: bool = True

    @property
    def vocabulary(self) -> Vocabulary:
        """Vocabulary canónico derivado del bundle (DEFAULT_VOCAB implícito)."""
        return Vocabulary(
            entities=set(self.entities),
            relations=set(self.relations),
            capabilities=set(self.capabilities),
        )

    @property
    def extended_entities(self) -> Set[str]:
        """Kinds que aportó el dominio (no estaban en DEFAULT_VOCAB)."""
        return set(self.entities) - DEFAULT_VOCAB.entities

    @property
    def extended_relations(self) -> Set[str]:
        return set(self.relations) - DEFAULT_VOCAB.relations

    @property
    def extended_capabilities(self) -> Set[str]:
        return set(self.capabilities) - DEFAULT_VOCAB.capabilities


__all__ = [
    "EntityMeta",
    "RelationMeta",
    "CapabilityMeta",
    "Entity",
    "Relation",
    "Capability",
    "Vocabulary",
    "DEFAULT_VOCAB",
    "is_canonical_kind",
    "OntologyValidator",
    "OntologyValidationError",
    "OntologyBundle",
    "validate_against_metamodel",
]
