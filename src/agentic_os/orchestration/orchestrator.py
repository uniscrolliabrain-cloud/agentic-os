from __future__ import annotations

import re
import uuid
from typing import Any, List, Optional, Tuple

from ..cognition.beliefs.belief import Belief
from ..cognition.planning.intent import Intent
from ..cognition.reasoning.proposer import LLMProposer, Proposer
from ..interfaces.llm.provider import BaseLLMProvider
from ..kernel.world.events import Event
from ..kernel.world.replay import replay
from ..cognition.roles.library import LIBRARY


class DeterministicIntentRouter:
    _ROUTES: Tuple[Tuple[Tuple[str, ...], str], ...] = (
        (("hello", "hi", "hey", "buenos dias", "buenas tardes", "buenas noches", "gracias"), "reply_to_user"),
        (("send email", "send an email", "send correo", "enviar email", "enviar un email", "enviar correo", "enviar un correo", "envia email", "envia un email", "envia correo", "envia un correo", "manda email", "manda un email", "manda correo", "manda un correo"), "send_email"),
        (("send slack", "send a slack", "enviar slack", "envia slack", "manda slack"), "send_slack"),
        (("send whatsapp", "send a whatsapp", "enviar whatsapp", "envia whatsapp", "manda whatsapp"), "send_whatsapp"),
        (("create event", "create an event", "create appointment", "schedule meeting", "agenda una reunion", "crear evento", "crear un evento", "crear cita", "crear una cita", "agendar reunion", "agendar una reunion", "programar reunion", "programar una reunion"), "create_event"),
        (("scrape web", "scrape website", "web scrape", "extraer pagina", "extraer una pagina", "scrapear web", "scrapear pagina", "scrapear una pagina"), "web_scrape"),
    )
    _ACCENTS = str.maketrans({"á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ü": "u", "ñ": "n"})

    @staticmethod
    def _normalize(message: str) -> str:
        normalized = (message or "").strip().lower().translate(DeterministicIntentRouter._ACCENTS)
        normalized = re.sub(r"[^a-z0-9\s]", " ", normalized)
        return re.sub(r"\s+", " ", normalized)

    def route(self, message: str) -> Optional[Intent]:
        normalized = self._normalize(message)
        for patterns, kind in self._ROUTES:
            if any(re.search(rf"\b{re.escape(pattern)}\b", normalized) for pattern in patterns):
                return Intent(
                    goal=message.strip(),
                    kind=kind,
                    entity_id="user-request",
                    payload={},
                    rationale="deterministic router",
                    confidence=1.0,
                )
        return None


class Orchestrator:
    def __init__(
        self,
        log: Any,
        llm: BaseLLMProvider,
        proposer: Optional[Proposer] = None,
        router: Optional[DeterministicIntentRouter] = None,
    ):
        """log acepta cualquier EventLogRepository (in-memory, JSONL o Postgres)."""
        self.log = log
        self.llm = llm
        self.proposer = proposer or LLMProposer(provider=llm)
        self.router = router or DeterministicIntentRouter()
        self.current_role = LIBRARY["director"]

    def tick(self):
        state = replay(self.log)
        return {"state": state, "role": self.current_role.name}

    def handle_user_message(
        self,
        user_message: str,
        tenant_id: str = "system",
        beliefs: Optional[List[Belief]] = None,
        domain_context: Optional[str] = None,
        correlation_id: Optional[str] = None,
        command_id: Optional[str] = None,
    ) -> Intent:
        """Propone una Intent determinista o mediante LLM y la audita."""
        role = self.current_role
        correlation_id = correlation_id or f"corr-{uuid.uuid4().hex}"
        command_id = command_id or f"cmd-{uuid.uuid4().hex}"

        routed = self.router.route(user_message)
        if routed is not None:
            intent = routed
            routing = "deterministic"
        else:
            role_context = (
                f"Role: {role.name}; permissions: {role.permissions}; "
                f"forbidden tools: {role.forbidden_tools or 'none'}."
            )
            proposer_context = (
                f"{domain_context}\n{role_context}" if domain_context else role_context
            )
            try:
                proposals = self.proposer.propose(
                    beliefs=beliefs or [],
                    goal=user_message,
                    domain_context=proposer_context,
                )
            except Exception:
                proposals = []
            intent = proposals[0] if proposals else Intent(
                goal=user_message.strip(),
                kind="reply_to_user",
                rationale="no proposal returned",
            )
            routing = "llm"

        self.log.append(
            Event(
                kind="IntentProposed",
                entity_id=intent.entity_id,
                payload={**intent.model_dump(mode="json"), "routing": routing},
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
        executor,
        registry=None,
        correlation_id=None,
        command_id=None,
        params=None,
    ):
        """Ejecuta un pipeline del catálogo vía PipelineRunner -> Executor.

        El Executor es obligatorio y se inyecta de forma explícita. El
        orquestador no construye un Executor interno ni ejecuta tools o
        connectors: cualquier efecto externo pasa por el Executor inyectado.
        `registry` se conserva por compatibilidad de call sites; la fuente
        de tools es `executor.registry`.
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
            raise TypeError(
                "handle_pipeline requiere un Executor inyectado; "
                "no se admite construcción interna ni ejecución directa"
            )

        if registry is not None and registry is not executor.registry:
            raise ValueError(
                "registry inyectado debe ser el mismo objeto que executor.registry"
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