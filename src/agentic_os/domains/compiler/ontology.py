"""Ontología del dominio `compiler` (FASE 1 — PLAN_CLINE_AGENTE_COMPILADOR.md).

Extiende el vocabulario del kernel con los kinds *de dominio* (namespace
``compiler.*``) sin tocar ``DEFAULT_VOCAB``. La compilación fail-closed
(``compile_ontology``) valida contra el metamodelo y produce un
``OntologyBundle`` versionado.
"""
from __future__ import annotations

from typing import Dict, Set

from ..base import BaseDomain
from .entities import (
    COMPILER_ENTITY_KINDS,
    CompilationRun,
    TenantBlueprint,
    TenantIdea,
)


class CompilerDomain(BaseDomain):
    """Dominio del compilador de tenants: ideas, blueprints y compilaciones."""

    domain: str = "compiler"
    entity_kinds: Set[str] = set(COMPILER_ENTITY_KINDS)
    relation_kinds: Set[str] = {
        "compiler.proposes",   # idea → blueprint
        "compiler.compiles",   # blueprint → run
    }
    capability_kinds: Set[str] = {
        "compiler.blueprint.generate",
        "compiler.tenant.compile",
    }

    @classmethod
    def register_entities(
        cls,
        registry: Dict[str, type] | None = None,
    ) -> None:
        """Registra las entidades del dominio en ENTITY_TYPE_REGISTRY.

        Camino canónico (docs/spec/01_ONTOLOGY.md, docs/INVARIANTS.md):
        primero compila la ontología fail-closed contra el metamodelo y
        después registra vía ``register_entity_types``. NUNCA como
        side-effect en import: el registro es una operación explícita de
        bootstrap, idempotente y fail-closed ante colisiones de kind.
        """
        from ...kernel.ontology.domain_models import register_entity_types

        cls.compile_ontology()  # fail-closed: vocabulario válido o no se registra
        register_entity_types(
            TenantIdea,
            TenantBlueprint,
            CompilationRun,
            registry=registry,
        )


__all__ = ["CompilerDomain"]
