from __future__ import annotations

from typing import Any, Dict, Optional

from ...infrastructure.idempotency import IdempotencyStore

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
        tenant_id: str,
        command_id: Optional[str],
        correlation_id: Optional[str],
        pipeline_id: str = "default",
        **kwargs,
    ) -> Dict[str, Any]:
        result = {"status": "OK", "pipeline_id": pipeline_id, "tenant_id": tenant_id}
        if command_id:
            try:
                self.idempotency.save(tenant_id or "system", f"pipeline:{command_id}", result)
            except Exception:
                pass
        return result

    def run(
        self,
        tenant_id: str = None,
        command_id: str = None,
        correlation_id: str = None,
        **kwargs,
    ) -> Dict[str, Any]:
        tid = tenant_id or "system"
        if command_id:
            try:
                cached = self.idempotency.get(tid, f"pipeline:{command_id}")
                if cached is not None:
                    return cached
            except Exception:
                pass
        return self._run_impl(tid, command_id, correlation_id, **kwargs)
