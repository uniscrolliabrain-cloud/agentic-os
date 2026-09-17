"""Handlers del tenant agentic-compiler.

En esta fase los pipelines estan DESHABILITADOS por diseno (enabled=False
en el modelo). Los handlers existen para documentar la forma, pero lanzan
NotImplementedError hasta que se implemente la Fase 3 del plan.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, Optional


def handle_blueprint_from_idea(runner: Any, tenant_id: str,
                               params: Dict[str, Any],
                               correlation_id: Optional[str]) -> Dict[str, Any]:
    raise NotImplementedError(
        "blueprint_from_idea se implementa en la Fase 3 del compilador; "
        "el pipeline esta deshabilitado hasta entonces."
    )


def handle_compile_tenant(runner: Any, tenant_id: str,
                          params: Dict[str, Any],
                          correlation_id: Optional[str]) -> Dict[str, Any]:
    raise NotImplementedError(
        "compile_tenant se implementa en la Fase 4; requiere sandbox + "
        "capabilities git/ci que aun no existen."
    )


HANDLERS: Dict[str, Callable[..., Dict[str, Any]]] = {
    "blueprint_from_idea": handle_blueprint_from_idea,
    "compile_tenant": handle_compile_tenant,
}

__all__ = ["HANDLERS"]