from __future__ import annotations

from typing import Any, Dict, Optional

from...infrastructure.idempotency import IdempotencyStore

class PipelineStepError(Exception):
    def __init__(self, tool_name: str, error: str):
        super().__init__(f"[pipeline] tool '{tool_name}' fallo: {error}")
        self.tool_name = tool_name
        self.error = error

class UnknownPipelineError(Exception):
    def __init__(self, pipeline_id: str):
        super().__init__(f"pipeline desconocido: {pipeline_id}")
        self.pipeline_id = pipeline_id

class PipelineRunner:
    def __init__(self, executor: Any, llm: Any = None):
        self.executor = executor
        self.idempotency = IdempotencyStore()
        self.llm = llm

    def emit_event(
        self,
        kind: str,
        entity_id: str,
        tenant_id: str,
        payload: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
        command_id: Optional[str] = None,
    ) -> None:
        """Emite un evento al EventLog (usado por pipelines para entity_created, etc.)."""
        if self.executor.event_log is None:
            return
        from ...kernel.world.events import Event

        event = Event(
            kind=kind,
            entity_id=entity_id,
            tenant_id=tenant_id,
            payload=payload or {},
            correlation_id=correlation_id,
            command_id=command_id,
        )
        self.executor.event_log.append(event)

    def tool(
        self,
        name: str,
        params: Dict[str, Any],
        tenant_id: str,
        correlation_id: Optional[str] = None,
        command_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        run_params = dict(params or {})
        if tenant_id:
            run_params.setdefault("tenant_id", tenant_id)

        result = self.executor.execute(
            action=name,
            params=run_params,
            tenant_id=tenant_id,
            correlation_id=correlation_id,
            command_id=command_id,
        )

        if not result.get("success"):
            raise PipelineStepError(name, result.get("error", "error desconocido"))

        output = result.get("output")
        if isinstance(output, dict):
            return output
        return {"data": output}

    def _run_impl(
        self,
        pipeline_id: str = "default",
        tenant_id: str = "system",
        params: Optional[Dict[str, Any]] = None,
        command_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        from . import PIPELINES, UnknownPipelineError

        if pipeline_id not in PIPELINES:
            raise UnknownPipelineError(pipeline_id)

        fn = PIPELINES[pipeline_id]
        try:
            result = fn(self, tenant_id, params or {}, correlation_id)
        except Exception as exc:
            raise PipelineStepError(pipeline_id, str(exc)) from exc

        if command_id:
            try:
                self.idempotency.save(tenant_id or "system", f"pipeline:{command_id}", result)
            except Exception:
                pass
        return result

    def run(
        self,
        pipeline_id: str = None,
        tenant_id: str = None,
        params: Optional[Dict[str, Any]] = None,
        command_id: str = None,
        correlation_id: str = None,
    ) -> Dict[str, Any]:
        tid = tenant_id or "system"
        pid = pipeline_id or "default"
        if command_id:
            try:
                cached = self.idempotency.get(tid, f"pipeline:{command_id}")
                if cached is not None:
                    return cached
            except Exception:
                pass
        return self._run_impl(
            pipeline_id=pid, tenant_id=tid, params=params,
            command_id=command_id, correlation_id=correlation_id,
        )
