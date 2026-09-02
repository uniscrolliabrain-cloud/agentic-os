from __future__ import annotations

from typing import Any, Dict, Optional

from ...kernel.world.events import Event


class PipelineStepError(Exception):

    def __init__(
        self,
        tool_name: str,
        error: str,
    ):
        super().__init__(
            f"[pipeline] tool '{tool_name}' "
            f"falló: {error}"
        )

        self.tool_name = tool_name
        self.error = error


class UnknownPipelineError(Exception):

    def __init__(
        self,
        pipeline_id: str,
    ):
        super().__init__(
            f"pipeline desconocido: {pipeline_id}"
        )

        self.pipeline_id = pipeline_id


class PipelineRunner:

    def __init__(
        self,
        executor: Any,
        llm: Any = None,
    ):
        self.executor = executor
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

            raise PipelineStepError(
                name,
                result.get(
                    "error",
                    "error desconocido",
                ),
            )

        output = result.get("output")

        if isinstance(output, dict):
            return output

        return {"data": output}

    def run(
        self,
        pipeline_id: str,
        tenant_id: str,
        params: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
        command_id: Optional[str] = None,
    ) -> Dict[str, Any]:

        from . import PIPELINES

        pipeline = PIPELINES.get(
            pipeline_id
        )

        if pipeline is None:
            raise UnknownPipelineError(
                pipeline_id
            )

        self._audit(
            "PipelineStarted",
            pipeline_id,
            tenant_id,
            correlation_id,
            command_id,
            {
                "pipeline_id": pipeline_id,
            },
        )

        try:

            result = pipeline(
                self,
                tenant_id,
                params or {},
                correlation_id,
            )

            self._audit(
                "PipelineCompleted",
                pipeline_id,
                tenant_id,
                correlation_id,
                command_id,
                {
                    "pipeline_id": pipeline_id,
                    "status": result.get("status"),
                },
            )

            return result

        except Exception as error:

            self._audit(
                "PipelineFailed",
                pipeline_id,
                tenant_id,
                correlation_id,
                command_id,
                {
                    "pipeline_id": pipeline_id,
                    "error": str(error)[:300],
                },
            )

            raise

    def _audit(
        self,
        kind: str,
        entity_id: str,
        tenant_id: str,
        correlation_id: Optional[str],
        command_id: Optional[str],
        payload: Dict[str, Any],
    ) -> None:

        event_log = getattr(
            self.executor,
            "event_log",
            None,
        )

        if event_log is None:
            return

        event_log.append(
            Event(
                kind=kind,
                entity_id=entity_id,
                tenant_id=tenant_id,
                actor_id="pipeline_runner",
                payload=payload,
                correlation_id=correlation_id,
                command_id=command_id,
            )
        )
