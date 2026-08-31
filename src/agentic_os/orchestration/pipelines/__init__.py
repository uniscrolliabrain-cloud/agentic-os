"""Pipelines de FASE 6: contenido social, leads->drafts e inbox watcher.

Cada pipeline executa una secuencia determinista de tools a través del
ToolRegistry/Executor (por eso el resultado SIEMPRE se audita). Recibe una
firma común: `run(executor, registry, tenant_id) -> dict`.
"""

from __future__ import annotations

from typing import Callable, Dict

PIPELINES: Dict[str, Callable] = {}


def register(pipeline_id: str) -> Callable:
    def decorator(fn: Callable) -> Callable:
        PIPELINES[pipeline_id] = fn
        return fn

    return decorator


# Importa los módulos para que se registren los pipelines
from .pipeline_daily_social import run_daily_social  # noqa: E402,F401
from .pipeline_leads_to_draft import run_leads_to_draft  # noqa: E402,F401
from .pipeline_inbox_watcher import run_inbox_watcher  # noqa: E402,F401

__all__ = ["PIPELINES", "register"]