"""domains.compiler: entidades y ontología del tenant «agentic-compiler» (FASE 1).

Sin side-effects en import: el registro de entidades en
``ENTITY_TYPE_REGISTRY`` es EXPLICITO, via ``CompilerDomain.register_entities()``
(camino canónico ``compile_ontology`` -> registro). Ver docs/INVARIANTS.md.
"""
from .entities import (
    COMPILER_ENTITY_KINDS,
    CompilationRun,
    TenantBlueprint,
    TenantIdea,
)
from .ontology import CompilerDomain

__all__ = [
    "COMPILER_ENTITY_KINDS",
    "CompilerDomain",
    "TenantIdea",
    "TenantBlueprint",
    "CompilationRun",
]
