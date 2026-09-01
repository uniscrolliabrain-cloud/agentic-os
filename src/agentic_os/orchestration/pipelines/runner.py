"""PipelineRunner: el mecanismo oficial para ejecutar pipelines (FASE de consolidación).

INVARIANTE: un pipeline NUNCA llama a una Tool directamente. Toda MicroAction
pasa SIEMPRE por `Executor.execute()` -> Policy -> Tool -> EventLog. Así un
pipeline no puede saltarse ni la política (default deny) ni la auditoría.

Flujo que garantiza:

    Pipeline -> MicroAction -> Policy -> Executor -> Tool -> EventLog
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from ...kernel.world.events import Event


class PipelineStepError(Exception):
    """Una MicroAction de un pipeline falló (denegada por policy, tool no
    registrada o error de la tool). El resultado del paso ya fue auditado."""

    def __init__(self, tool_name: str, error: str):
        super().__init__(f"[pipeline] tool '{tool_name}' falló: {error}")
        self.tool_name = tool_name
        self.error = error


class UnknownPipelineError(Exception):
    def __init__(self, pipeline_id: str):
        super().__init__(f"pipeline desconocido: {pipeline_id}")
        self.pipeline_id = pipeline_id


class PipelineRunner:
    """Ejecuta pipelines declarados en `orchestration.pipelines.PIPELINES`.

    `executor` es SIEMPRE la instancia canónica de `Executor` (con su
    PolicyEngine y su EventLog). No existe un segundo executor.
    """

    def __init__(self, executor: Any, llm: Any = None):
        self.executor = executor
        self.llm = llm  # LLM opcional para pasos de razonamiento (copy, clasificación)

    # ----------------------------------------------------------- interface --
    def tool(self, name: str, params: Dict[str, Any], tenant_id: str,
             correlation_id: Optional[str] = None) -> Dict[str, Any]:
        """Ejecuta una MicroAction por el camino oficial (Executor -> Policy -> Tool)."""
        result = self.executor.execute(
            action=name,
            params=params,
            context=None,
            tenant_id=tenant_id,
            correlation_id=correlation_id,
        )
        if not result.get("success"):
            raise PipelineStepError(name, result.get("error") or "desconocido")
        output = result.get("output") or {}
        return output if isinstance(output, dict) else {"data": output}

    def run(self, pipeline_id: str, tenant_id: str, params: Optional[Dict[str, Any]] = None,
            correlation_id: Optional[str] = None) -> Dict[str, Any]:
        """Ejecuta el pipeline completo, auditando PipelineStarted -> PipelineCompleted/Failed."""
        from . import PIPELINES

        fn = PIPELINES.get(pipeline_id)
        if fn is None:
            raise UnknownPipelineError(pipeline_id)

        self._audit("PipelineStarted", pipeline_id, tenant_id, correlation_id,
                    {"pipeline_id": pipeline_id})
        try:
            result = fn(self, tenant_id, params or {}, correlation_id)
        except Exception as exc:  # noqa: BLE001 - el runner convierte fallo en evento + re-lanza
            self._audit("PipelineFailed", pipeline_id, tenant_id, correlation_id,
                        {"pipeline_id": pipeline_id, "error": str(exc)[:300],
                         # nunca convertir un fallo real en éxito
                         "fallback_success": False})
            raise
        self._audit("PipelineCompleted", pipeline_id, tenant_id, correlation_id,
                    {"pipeline_id": pipeline_id, "status": result.get("status")})
        return result

    # ------------------------------------------------------------ auditoría --
    def _audit(self, kind: str, entity_id: str, tenant_id: str,
               correlation_id: Optional[str], payload: Dict[str, Any]) -> None:
        log = getattr(self.executor, "event_log", None)
        if log is None:
            return
        try:
            log.append(Event(
                kind=kind,
                entity_id=entity_id,
                tenant_id=tenant_id or "system",
                actor_id="pipeline_runner",
                payload=payload,
                correlation_id=correlation_id,
            ))
        except Exception:  # noqa: BLE001 - auditar nunca rompe el flujo
            pass