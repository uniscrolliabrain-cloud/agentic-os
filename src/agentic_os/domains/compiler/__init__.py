"""domains.compiler: tenant `agentic-compiler`."""
from .entities import (
    COMPILER_ENTITY_KINDS,
    CompilationRun,
    TenantBlueprint,
    TenantIdea,
)
from .handlers import HANDLERS
from .ontology import CompilerDomain
from .pipelines import PIPELINES, CompilerPipeline, CompilerStep
from .sops import SOPS, SOP


class _CompilerDomainPack:
    slug = "agentic-compiler"
    pipelines = PIPELINES
    handlers = HANDLERS
    sops = SOPS

    @staticmethod
    def register_entities() -> None:
        CompilerDomain.register_entities()


DOMAIN = _CompilerDomainPack()

__all__ = [
    "DOMAIN",
    "COMPILER_ENTITY_KINDS",
    "CompilerDomain",
    "TenantIdea",
    "TenantBlueprint",
    "CompilationRun",
    "PIPELINES",
    "CompilerPipeline",
    "CompilerStep",
    "SOPS",
    "SOP",
    "HANDLERS",
]