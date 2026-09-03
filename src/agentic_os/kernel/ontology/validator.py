from __future__ import annotations
from typing import Iterable
from .entities import Entity
from .relations import Relation
from .invariants import OntologyViolation, validate_relation
from .vocabulary import Vocabulary, DEFAULT_VOCAB


class OntologyValidationError(ValueError):
    """Agrega todos los errores estructurales de una ontología inválida."""


class OntologyValidator:
    """Validador determinista de ontologías (el LLM nunca decide aquí).

    Comprueba: estructura de entidades, estructura de relaciones,
    pertenencia al Vocabulary, referencias (src/dst existen) y las
    invariantes ejecutables declaradas en invariants.py.
    """

    def __init__(self, vocab: Vocabulary = DEFAULT_VOCAB):
        self.vocab = vocab

    def validate_entity(self, e: Entity) -> bool:
        return e.kind in self.vocab.entities

    def validate_relation(self, r: Relation) -> bool:
        return r.kind in self.vocab.relations

    def validate(
        self,
        entities: Iterable[Entity],
        relations: Iterable[Relation],
    ) -> None:
        """Valida una ontología completa; lanza OntologyValidationError
        agregando todos los errores encontrados (fail-fast no: reporte
        completo, determinista)."""
        errors: list[str] = []
        entity_map: dict[str, Entity] = {}

        for e in entities:
            if e.id in entity_map:
                errors.append(f"entidad duplicada: {e.id!r}")
                continue
            entity_map[e.id] = e
            if not self.validate_entity(e):
                errors.append(
                    f"entidad {e.id!r} con kind fuera del Vocabulary: {e.kind!r}"
                )

        relation_list = list(relations)
        seen_ids: set[str] = set()
        for r in relation_list:
            if r.id in seen_ids:
                errors.append(f"relación duplicada: {r.id!r}")
            seen_ids.add(r.id)
            if not self.validate_relation(r):
                errors.append(
                    f"relación {r.id!r} con kind fuera del Vocabulary: {r.kind!r}"
                )
                continue
            try:
                validate_relation(entity_map, r)
            except OntologyViolation as exc:
                errors.append(f"relación {r.id!r}: {exc}")

        if errors:
            raise OntologyValidationError(
                "ontología inválida:\n- " + "\n- ".join(errors)
            )

