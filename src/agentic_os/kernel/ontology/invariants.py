"""Invariantes de la ontología (documentación + validaciones ejecutables).

Las reglas declaradas en INVARIANTS se aplican con funciones deterministas:
el LLM nunca decide si una ontología es válida.
"""
from __future__ import annotations

from typing import Mapping

from .entities import Entity
from .relations import Relation


INVARIANTS = [
    "Actor -> uses -> Tool",
    "Tool -> accesses -> Resource",
    "Capability -> requires -> Tool",
    "Policy -> governs -> Capability",
    "WorldState derivable",
    "Event immutable",
]


class OntologyViolation(ValueError):
    """Se lanza cuando una relación viola una invariante de la ontología."""


# Semántica de relaciones validables sobre el vocabulario de entidades.
# 'policy' y 'capability' son categorías conceptuales (no entity kinds del
# Vocabulary), por eso no aparecen aquí: esas reglas se dejan documentadas
# hasta que existan entity kinds para ellas.
_RELATION_SEMANTICS: dict[str, tuple[set[str], set[str]]] = {
    "uses": ({"actor", "user", "agent"}, {"tool"}),
    "accesses": ({"tool"}, {"resource"}),
    "requires": ({"tool"}, {"tool"}),
    "belongs_to": ({"tool", "resource", "event", "goal"}, {"actor", "user", "agent"}),
    "triggers": ({"event", "goal"}, {"tool", "goal", "event"}),
}


def validate_relation(
    entity_map: Mapping[str, Entity],
    relation: Relation,
) -> None:
    """Valida la semántica src/kind/dst de una relación contra la ontología.

    Lanza OntologyViolation si la relación viola una invariante declarada o
    referencia entidades desconocidas.
    """
    source = entity_map.get(relation.src_id)
    target = entity_map.get(relation.dst_id)

    if source is None:
        raise OntologyViolation(
            f"relación {relation.kind!r} referencia src_id desconocido: {relation.src_id!r}"
        )
    if target is None:
        raise OntologyViolation(
            f"relación {relation.kind!r} referencia dst_id desconocido: {relation.dst_id!r}"
        )

    semantics = _RELATION_SEMANTICS.get(relation.kind)
    if semantics is None:
        # kind sin semántica declarada (p.ej. 'governs' conceptual): nada que
        # validar estructuralmente aquí; la pertenencia al Vocabulary la
        # comprueba OntologyValidator.
        return

    src_kinds, dst_kinds = semantics
    if source.kind not in src_kinds:
        raise OntologyViolation(
            f"invariante violada para {relation.kind!r}: src esperado "
            f"{sorted(src_kinds)}, recibido {source.kind!r}"
        )
    if target.kind not in dst_kinds:
        raise OntologyViolation(
            f"invariante violada para {relation.kind!r}: dst esperado "
            f"{sorted(dst_kinds)}, recibido {target.kind!r}"
        )


def validate_all_relations(
    entity_map: Mapping[str, Entity],
    relations,
) -> None:
    """Aplica validate_relation a todas las relaciones (determinista)."""
    for relation in relations:
        validate_relation(entity_map, relation)

