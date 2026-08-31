from __future__ import annotations

from typing import Any

from ..kernel.world.replay import replay
from ..kernel.world.events import Event
from ..cognition.roles.library import LIBRARY
from ..cognition.planning.intent import Intent
from ..interfaces.llm.provider import BaseLLMProvider


class Orchestrator:
    def __init__(self, log: Any, llm: BaseLLMProvider):
        """`log` acepta cualquier EventLogRepository (in-memory, JSONL o
        Postgres). FASE 3.1: tick()/replay usan la interfaz común
        all_events(), nunca el atributo concreto `.events`."""
        self.log = log
        self.llm = llm
        self.current_role = LIBRARY["director"]

    def tick(self):
        state = replay(self.log)
        return {"state": state, "role": self.current_role.name}

    def handle_user_message(self, user_message: str, tenant_id: str = "system") -> Intent:
        """
        El usuario escribe algo en el chat -> el rol activo (director) propone
        una Intent -> se guarda como evento en el log (auditable) -> se devuelve
        para que la capa siguiente (policy + executor) decida si se ejecuta.

        `tenant_id` es obligatorio para el aislamiento multi-tenant: el evento
        queda etiquetado al tenant que generó la conversación.

        Este método NUNCA ejecuta nada por sí mismo: solo produce una propuesta.
        """
        role = self.current_role

        system_instruction = (
            f"Eres el rol '{role.name}' dentro de un sistema agéntico. "
            f"Tus permisos son: {role.permissions}. "
            f"Tienes PROHIBIDO usar estas herramientas: {role.forbidden_tools or 'ninguna restricción adicional'}. "
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
            )
        )

        return intent

    def handle_pipeline(self, pipeline_id: str, tenant_id: str, executor=None, registry=None) -> dict:
        """FASE 6: ejecuta un pipeline programado (daily_social, inbox_watcher...).

        El scheduler (o cualquier trigger) llama a este método; el pipeline se
        resuelve desde el catálogo `orchestration/pipelines` y se ejecuta con
        el registry de tools del tenant.
        """
        from .pipelines import PIPELINES

        if pipeline_id not in PIPELINES:
            self.log.append(
                Event(
                    kind="ScheduledPipelineFailed",
                    entity_id=f"pipeline://{pipeline_id}",
                    tenant_id=tenant_id,
                    actor_id="scheduler",
                    payload={"error": f"pipeline desconocido: {pipeline_id}"},
                )
            )
            return {"status": "UNKNOWN_PIPELINE", "pipeline_id": pipeline_id}

        if registry is None:
            registry = self._default_registry()
        if executor is None:
            executor = _PipelineExecutorHost(llm=self.llm, registry=registry)
        fn = PIPELINES[pipeline_id]
        return fn(executor, registry, tenant_id)

    def _default_registry(self):
        """Registry por defecto (mocks + bridge) para ejecutar pipelines en
        ausencia de un registry inyectado por la API."""
        from ..execution.tools import build_default_registry

        return build_default_registry()


class _PipelineExecutorHost:
    """Host mínimo para que los pipelines lean `_llm` y ejecuten tools sin
    depender de la API (usado en tests y en el orquestador)."""

    def __init__(self, llm=None, registry=None):
        self._llm = llm
        self._pipeline_params = {}
        self.registry = registry
