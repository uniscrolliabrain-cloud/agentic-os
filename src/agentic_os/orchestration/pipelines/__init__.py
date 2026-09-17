"""Paquete pipelines - solo re-exporta el motor tenant-agnostico.

Los pipelines REALES viven en `domains/<tenant>/pipelines.py`.
Ver docs/TENANTS.md.
"""
from .runner import (
    PipelineRunner,
    PipelineStepError,
    UnknownPipelineError,
    get_tenant_handlers,
    get_tenant_pipelines,
    list_registered_tenants,
)

__all__ = [
    "PipelineRunner",
    "PipelineStepError",
    "UnknownPipelineError",
    "get_tenant_handlers",
    "get_tenant_pipelines",
    "list_registered_tenants",
]