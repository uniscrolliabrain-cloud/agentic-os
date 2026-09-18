"""TemporalStub (BUILD_PLAN 0b). Misma interfaz que Temporal, sin Temporal.

Cuando ENABLE_TEMPORAL=false, el sistema usa este stub:
- start_workflow() ejecuta inline y devuelve un handle simulado.
- get_client() devuelve el stub si el flag esta off, o el cliente real
  si esta on.

Objetivo: el codigo del orquestador no sabe si Temporal esta on u off.
Los contratos son los mismos.
"""
from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict, Optional

from pydantic import BaseModel, ConfigDict


class StubWorkflowHandle(BaseModel):
    """Handle simulado de workflow. Cumple la interfaz minima."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    result: Optional[Any] = None


class TemporalStub:
    """Stub que simula Temporal ejecutando la coroutine inline."""

    def __init__(self) -> None:
        self._counter = 0

    async def start_workflow(
        self,
        workflow_name: str,
        args: Optional[list] = None,
        id: Optional[str] = None,
        task_queue: Optional[str] = None,
    ) -> StubWorkflowHandle:
        """Simula el arranque de un workflow. No ejecuta nada todavia."""
        self._counter += 1
        wf_id = id or f"stub-wf-{self._counter}"
        return StubWorkflowHandle(id=wf_id, result=None)

    async def execute_activity(
        self,
        activity: Callable[..., Awaitable[Any]],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Ejecuta la activity inline. Unico punto que "hace" trabajo."""
        return await activity(*args, **kwargs)


async def get_temporal_client() -> Any:
    """Devuelve cliente real si ENABLE_TEMPORAL=true, stub si no.

    Fail-safe: si el flag esta on pero el import falla, degrada a stub.
    """
    from ...infrastructure.config.feature_flags import flags

    if not flags.temporal:
        return TemporalStub()

    try:
        from .client import get_client as _real_get_client

        return await _real_get_client()
    except Exception:
        return TemporalStub()


__all__ = ["StubWorkflowHandle", "TemporalStub", "get_temporal_client"]

