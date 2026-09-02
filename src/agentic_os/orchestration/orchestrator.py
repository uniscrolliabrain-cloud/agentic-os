from __future__ import annotations

import uuid
from typing import Any

from ..kernel.world.replay import replay
from ..kernel.world.events import Event
from ..cognition.roles.library import LIBRARY
from ..cognition.planning.intent import Intent
from ..interfaces.llm.provider import BaseLLMProvider


class Orchestrator:
    def __init__(self, log: Any, llm: BaseLLMProvider):
        """log acepta cualquier EventLogRepository (in-memory, JSONL o Postgres)."""
        self.log = log
        self.llm = llm
        self.current_role = LIBRARY["director"]

    def tick(self):
        state = replay(self.log)
        return {"state": state, "role": self.current_role.name}

    def handle_user_message(self, user_message: str, tenant_id: str = "system") -> Intent:
        """El rol activo (director) propone una Intent y la audita en el log.

        Hardening: se generan correlation_id y command_id y se propagan en el
        Event para que toda la ejecucion posterior sea reconstruible.
        """
        role = self.current_role
        correlation_id = f"corr-{uuid.uuid4().hex}"
        command_id = f"cmd-{uuid.uuid4().hex}"

        system_instruction = (
            f"Eres el rol '{role.name}' dentro de un sistema agentico. "
            f"Tus permisos son: {role.permissions}. "
            f"Tienes PROHIBIDO usar estas herramientas: "
            f"{role.forbidden_tools or 'ninguna restriccion adicional'}. "
            "No ejecutas nada directamente: solo propones una Intent estructurada. "
            "Si el usuario solo quiere charlar o preguntar algo, usa kind='reply_to_user' "
            "y pon tu respuesta en el campo reply_to_user."
        )

        intent = self.llm.generate_structured(
            prompt=user_message,
            response_schema=Intent,
            system_instruction=system_instruction,
        )

        self.log.append(
            Event(
                kind="IntentProposed",
                entity_id=intent.entity_id,
                payload=intent.model_dump(),
                actor_id=role.name,
                tenant_id=tenant_id,
                correlation_id=correlation_id,
                command_id=command_id,
            )
        )

        return intent

    def handle_pipeline(
        self,
        pipeline_id: str,
        tenant_id: str,
        executor=None,
        registry=None,
        correlation_id=None,
        command_id=None,
        params=None,
    ):
        """FASE 6: ejecuta un pipeline programado con TenantContext obligatorio.

        El trigger (scheduler/API) llama a este método; el pipeline se resuelve
        del catálogo y se ejecuta SIEMPRE via PipelineRunner -> Executor ->
        Policy -> Tool -> EventLog (auditando PipelineStarted/Completed/Failed).
        """
        from .pipelines import PIPELINES

        if pipeline_id not in PIPELINES:
            self.log.append(
                Event(
                    kind="ScheduledPipelineFailed",
                    entity_id=f"pipeline://{pipeline_id}",
                    tenant_id=tenant_id,
                    actor_id="orchestrator",
                    payload={"error": f"pipeline desconocido: {pipeline_id}"},
                    correlation_id=correlation_id,
                    command_id=command_id,
                )
            )
            return {"status": "UNKNOWN_PIPELINE", "pipeline_id": pipeline_id}

        if executor is None:
            from ..execution.executor import Executor

            executor = Executor(
                registry=registry or self._default_registry(),
                event_log=self.log,
            )

        from .pipelines.runner import PipelineRunner
        from .pipelines.validation import assert_catalog_valid

        runner = PipelineRunner(executor=executor, llm=self.llm)
        assert_catalog_valid(executor.registry)

        return runner.run(
            pipeline_id=pipeline_id,
            tenant_id=tenant_id,
            params=params or {},
            correlation_id=correlation_id,
            command_id=command_id,
        )

    def _default_registry(self):
        """Registry por defecto (mocks + bridge) para pipelines sin registry propio."""
        from ..execution.tools import build_default_registry

        return build_default_registry()


class _PipelineExecutorHost:
    """Host minimo para pipelines legacy: expone _llm y tool()."""

    def __init__(self, llm=None, registry=None):
        self._llm = llm
        self.llm = llm
        self._pipeline_params = {}
        self.registry = registry

    def tool(self, name: str, params: dict, tenant_id: str = "system", correlation_id: Any = None) -> dict:
        if self.registry:
            t = self.registry.get(name)
            if t:
                run_params = dict(params or {})
                if tenant_id:
                    run_params.setdefault("tenant_id", tenant_id)
                return t.run(run_params)
        raise ValueError(f"Tool '{name}' no encontrada en registry")