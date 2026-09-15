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
    """Unico camino canonico para ejecutar pipelines + cognicion episodica.

    Respeta tu firma existente:
      run(tenant_id, command_id, correlation_id, pipeline_id, **kwargs)
      _run_impl(tenant_id, command_id, correlation_id, pipeline_id, **kwargs)
    """

    def __init__(self, executor: Any, llm: Any = None, cognition_registry: Any = None):
        self.executor = executor
        self.idempotency = IdempotencyStore()
        self.llm = llm
        # CognitionRegistry perezoso para no romper si el modulo aun no existe
        self._cognition_registry = cognition_registry
        if self._cognition_registry is None:
            try:
                from ...cognition.memory import CognitionRegistry

                self._cognition_registry = CognitionRegistry()
            except Exception:
                self._cognition_registry = None

    def _cognition(self, tenant_id: str, agent_id: str):
        if self._cognition_registry is None:
            return None
        try:
            return self._cognition_registry.for_agent(tenant_id, agent_id)
        except Exception:
            return None

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

    # ------------------------------------------------------------------
    # Implementacion real (con auditoria + idempotencia)
    # ------------------------------------------------------------------
    def _run_impl(
        self,
        tenant_id: str,
        command_id: Optional[str],
        correlation_id: Optional[str],
        pipeline_id: str = "default",
        **kwargs,
    ) -> Dict[str, Any]:
        # Import diferido: los modulos se registran via @register al importar el paquete
        from . import PIPELINES

        # Soporte para que llames run(pipeline_id="daily_social") o run("daily_social")
        # Tu archivo original esperaba pipeline_id en kwargs o posicional
        params = kwargs.get("params") or {}
        if isinstance(kwargs.get("pipeline_id"), str):
            pipeline_id = kwargs.get("pipeline_id")

        # Permitir que el primer arg sea pipeline_id si lo pasan como tenant_id por error comun
        # Normalizamos: si tenant_id parece un pipeline_id conocido, lo movemos
        if tenant_id in PIPELINES and pipeline_id == "default":
            pipeline_id = tenant_id
            tenant_id = kwargs.get("tenant_id") or "system"

        tid = tenant_id or "system"

        pipeline = PIPELINES.get(pipeline_id)
        if pipeline is None:
            raise UnknownPipelineError(pipeline_id)

        # --- Cognition: episodic pipeline_started ---
        cog = self._cognition(tid, pipeline_id)
        if cog is not None:
            try:
                cog.episodic_append(
                    event_type="pipeline_started",
                    payload={"pipeline_id": pipeline_id, "param_keys": sorted(params.keys()) if isinstance(params, dict) else []},
                    correlation_id=correlation_id,
                )
            except Exception:
                pass

        try:
            # Tu pipeline_daily_social etc esperan firma: (runner, tenant_id, params, correlation_id)
            result = pipeline(self, tid, params, correlation_id)

            if not isinstance(result, dict):
                result = {"status": "OK", "data": result, "pipeline_id": pipeline_id, "tenant_id": tid}

            if command_id:
                try:
                    self.idempotency.save(tid, f"pipeline:{command_id}", result)
                except Exception:
                    pass

            if cog is not None:
                try:
                    cog.episodic_append(
                        event_type="pipeline_completed",
                        payload={"pipeline_id": pipeline_id, "status": result.get("status", "unknown")},
                        correlation_id=correlation_id,
                    )
                except Exception:
                    pass

            return result

        except Exception as error:
            if cog is not None:
                try:
                    cog.episodic_append(
                        event_type="pipeline_failed",
                        payload={"pipeline_id": pipeline_id, "error": str(error)[:500]},
                        correlation_id=correlation_id,
                    )
                except Exception:
                    pass
            raise

    def run(
        self,
        tenant_id: str = None,
        command_id: str = None,
        correlation_id: str = None,
        **kwargs,
    ) -> Dict[str, Any]:
        # Caso 1: run(pipeline_id="daily_social", tenant_id="t1")
        # Caso 2: run("daily_social", tenant_id="t1") -> tu firma antigua tenia tenant_id primero
        # Caso 3: run(tenant_id="t1", pipeline_id="daily_social")
        pipeline_id = kwargs.pop("pipeline_id", None)

        # Si el primer arg es un pipeline conocido y no se paso pipeline_id explicito
        from . import PIPELINES as _PIPELINES  # import perezoso

        if tenant_id in _PIPELINES and pipeline_id is None:
            pipeline_id = tenant_id
            tenant_id = kwargs.pop("tenant_id", None) or "system"

        if pipeline_id is None:
            pipeline_id = kwargs.pop("pipeline_id", None) or "default"

        tid = tenant_id or kwargs.get("tenant_id") or "system"

        if command_id:
            try:
                cached = self.idempotency.get(tid, f"pipeline:{command_id}")
                if cached is not None:
                    return cached
            except Exception:
                pass

        return self._run_impl(tid, command_id, correlation_id, pipeline_id, **kwargs)
