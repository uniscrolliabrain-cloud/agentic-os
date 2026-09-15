"""cognition.agents: contratos y catálogo del sistema de miniagentes.

Fuente de verdad tipada de la spec docs/spec/07_PYDANTIC_CONTRACTS.md.
"""
from .catalog import Catalog, CatalogError
from .schemas import (
    MicroActionSchema,
    MiniAgentSchema,
    PipelineSchema,
    PipelineStep,
    TaskNode,
    TaskPlan,
)

__all__ = [
    "Catalog",
    "CatalogError",
    "MicroActionSchema",
    "MiniAgentSchema",
    "PipelineSchema",
    "PipelineStep",
    "TaskNode",
    "TaskPlan",
]
