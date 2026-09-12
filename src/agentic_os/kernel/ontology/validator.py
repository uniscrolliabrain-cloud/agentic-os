from __future__ import annotations

from typing import TYPE_CHECKING, Any, Iterable

from .entities import Entity
from .relations import Relation
from .invariants import OntologyViolation, validate_relation
from .vocabulary import Vocabulary, DEFAULT_VOCAB, is_canonical_kind

if TYPE_CHECKING:
    from . import OntologyBundle


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

    @classmethod
    def from_bundle(cls, bundle: "OntologyBundle") -> "OntologyValidator":
        """Construye un validador a partir de un OntologyBundle congelado."""
        return cls(vocab=bundle.vocabulary)

    def validate_entity(self, e: Entity[Any]) -> bool:
        return e.kind in self.vocab.entities

    def validate_relation(self, r: Relation) -> bool:
        return r.kind in self.vocab.relations

    def validate(
        self,
        entities: Iterable[Entity[Any]],
        relations: Iterable[Relation],
    ) -> None:
        """Valida una ontología completa; lanza OntologyValidationError
        agregando todos los errores encontrados (fail-fast no: reporte
        completo, determinista)."""
        errors: list[str] = []
        entity_map: dict[str, Entity[Any]] = {}

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
                continue
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


def validate_against_metamodel(
    entity_kinds: Iterable[str] = (),
    relation_kinds: Iterable[str] = (),
    capability_kinds: Iterable[str] = (),
    entities: Iterable[Entity[Any]] = (),
    relations: Iterable[Relation] = (),
    tenant_scope: str = "",
    default_vocab: Vocabulary = DEFAULT_VOCAB,
) -> "OntologyBundle":
    """Valida las declaraciones de vocabulario de un dominio contra el metamodelo.

    Punto de entrada canónico: ``tenant → declara ontología Pydantic → kernel
    valida contra metamodelo → acepta/rechaza``.  El LLM **nunca** registra un
    esquema directamente en runtime.

    Rechaza explícitamente (``OntologyValidationError``) si:
      1. algún *kind* no es un slug canónico (p. ej. ``Actor``, ``x/y``).
      2. alguna entidad/relación/capacidad colisiona con DEFAULT_VOCAB
         (un dominio extiende, no reemplaza).
      3. alguna relación de instancia referencia entidades no declaradas
         en el propio bundle del tenant.

    Devuelve un :class:`OntologyBundle` frozen + versionado si pasa.
    """
    # Late import: OntologyBundle vive en ontology/__init__.py, que a su vez
    # importa este módulo.  La importación diferida rompe el ciclo.
    from . import OntologyBundle

    errors: list[str] = []

    ent_kinds = set(entity_kinds)
    rel_kinds = set(relation_kinds)
    cap_kinds = set(capability_kinds)

    # --- 1. slug canónico ---
    for kind in ent_kinds:
        if not is_canonical_kind(kind):
            errors.append(f"entity kind no canónico: {kind!r}")
    for kind in rel_kinds:
        if not is_canonical_kind(kind):
            errors.append(f"relation kind no canónico: {kind!r}")
    for kind in cap_kinds:
        if not is_canonical_kind(kind):
            errors.append(f"capability kind no canónico: {kind!r}")

    # --- 2. colisión con DEFAULT_VOCAB (extiende, no reemplaza) ---
    ent_collision = ent_kinds & default_vocab.entities
    if ent_collision:
        errors.append(
            f"colisión con DEFAULT_VOCAB (entities): {sorted(ent_collision)} — "
            "un dominio no puede redefinir kinds canónicos del kernel"
        )
    rel_collision = rel_kinds & default_vocab.relations
    if rel_collision:
        errors.append(
            f"colisión con DEFAULT_VOCAB (relations): {sorted(rel_collision)}"
        )
    cap_collision = cap_kinds & default_vocab.capabilities
    if cap_collision:
        errors.append(
            f"colisión con DEFAULT_VOCAB (capabilities): {sorted(cap_collision)}"
        )

    # --- 3. relaciones de instancia referencian entities declaradas ---
    entity_list = list(entities)
    rel_list = list(relations)
    entity_ids: set[str] = {e.id for e in entity_list}
    for r in rel_list:
        if r.src_id not in entity_ids:
            errors.append(
                f"relación {r.id!r} referencia src_id no declarado: {r.src_id!r}"
            )
        if r.dst_id not in entity_ids:
            errors.append(
                f"relación {r.id!r} referencia dst_id no declarado: {r.dst_id!r}"
            )

    if errors:
        raise OntologyValidationError(
            "ontología inválida:\n- " + "\n- ".join(errors)
        )

    extended = Vocabulary(
        entities=default_vocab.entities | ent_kinds,
        relations=default_vocab.relations | rel_kinds,
        capabilities=default_vocab.capabilities | cap_kinds,
    )

    return OntologyBundle(
        version=1,
        tenant_scope=tenant_scope,
        entities=set(extended.entities),
        relations=set(extended.relations),
        capabilities=set(extended.capabilities),
        frozen=True,
    )
