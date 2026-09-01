"""Pipelines de FASE 6: contenido social, leads->drafts e inbox watcher.

Cada pipeline ejecuta MicroActions mediente el mecanismo oficial del sistema:
el `PipelineRunner` pasa SIEMPRE por `Executor` (Policy + auditoría). Un
pipeline NUNCA llama a una Tool directamente (violaría el invariante
Pipeline -> MicroAction -> Policy -> Executor -> Tool -> EventLog).
"""

from __future__ import annotations

from typing import Callable, Dict, List, Optional

PIPELINES: Dict[str, Callable] = {}
PIPELINE_TOOLS: Dict[str, List[str]] = {}


def register(pipeline_id: str, tools: Optional[List[str]] = None) -> Callable:
    """Registra un pipeline y las MicroActions/Tools que declara usar.

    `tools` es la declaración de dependencias del pipeline (la usa el
    validador de catálogo para detectar referencias rotas antes de runtime).
    """

    def decorator(fn: Callable) -> Callable:
        PIPELINES[pipeline_id] = fn
        PIPELINE_TOOLS[pipeline_id] = list(tools or [])
        return fn

    return decorator


# Importa los módulos para que se registren los pipelines
from .pipeline_daily_social import run_daily_social  # noqa: E402,F401
from .pipeline_leads_to_draft import run_leads_to_draft  # noqa: E402,F401
from .pipeline_inbox_watcher import run_inbox_watcher  # noqa: E402,F401
from .runner import PipelineRunner, PipelineStepError, UnknownPipelineError  # noqa: E402,F401
from .validation import validate_pipeline_tools  # noqa: E402,F401

__all__ = ["PIPELINES", "PIPELINE_TOOLS", "register", "PipelineRunner",
           "PipelineStepError", "UnknownPipelineError", "validate_pipeline_tools"]