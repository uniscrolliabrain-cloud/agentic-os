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
        # ESCRIBIR / ENVIAR
        (("send email", "enviar email", "envia email", "envia un email", "enviar un email", "manda email", "manda un email", "enviar correo", "envia correo", "envia un correo", "manda correo", "manda un correo"), "email.message.send"),
        (("send slack", "enviar slack", "envia slack", "manda slack"), "communication.message.send"),
        (("send whatsapp", "enviar whatsapp", "envia whatsapp", "manda whatsapp"), "whatsapp.message.send"),
        # CALENDARIO
        (("create event", "crear evento", "crear un evento", "crear cita", "crear una cita", "agendar reunion", "agenda una reunion", "agendar una reunion", "programar reunion", "schedule meeting"), "calendar.event.create"),
        (("ver calendario", "mi calendario", "proximos eventos", "lista de eventos", "listar eventos", "mis eventos", "que eventos"), "calendar.event.read"),
        # LEER / LISTAR
        (("leer correos", "lee correos", "lee los correos", "lee los ultimos", "ver correos", "mis correos", "mi bandeja", "leer bandeja", "lee la bandeja", "correos sin leer", "ultimos correos", "buzon", "inbox"), "email.message.read"),
        (("listar drive", "lista drive", "mis ficheros", "mis archivos", "mi drive", "ver drive", "ver mis ficheros", "ver mis archivos", "listar ficheros", "listar archivos"), "file.read"),
        # WEB
        (("scrape web", "scrapear", "extraer pagina", "extraer una pagina"), "web.page.extract"),
        (("buscar en la web", "busca en la web", "buscar web", "googlea", "search web"), "web.search"),
    )
    _ACCENTS = str.maketrans({"a": "a", "e": "e", "i": "i", "o": "o", "u": "u", "n": "n"})

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
        """Ejecuta un pipeline del catalogo del tenant via PipelineRunner.

        El Executor es obligatorio y se inyecta explicitamente. El orquestador
        no construye Executor interno ni ejecuta tools/connectors.

        Orden de validacion (fail-closed, deterministico):
          1. executor inyectado (nunca se construye dentro)
          2. registry, si se inyecta, es el mismo que executor.registry
          3. pipeline existe en el catalogo del tenant
          4. catalogo del tenant consistente (tools referenciadas existen)
          5. ejecutar via PipelineRunner
        """
        # 1) Contrato: el Executor SIEMPRE es obligatorio (fail-closed)
        if executor is None:
            raise TypeError(
                "handle_pipeline requiere un Executor inyectado; "
                "no se admite construccion interna ni ejecucion directa"
            )

        # 2) Registry inyectado debe ser el mismo objeto que executor.registry
        if registry is not None and registry is not executor.registry:
            raise ValueError(
                "registry inyectado debe ser el mismo objeto que executor.registry"
            )

        from .pipelines.runner import (
            PipelineRunner,
            get_tenant_pipelines,
        )
        from .pipelines.validation import assert_tenant_catalog_valid

        # 3) Resolver tenant_slug desde TenantRegistry (si existe)
        tenant_slug = tenant_id
        try:
            from ..infrastructure.tenancy import TenantRegistry
            t = TenantRegistry().get(tenant_id)
            if t is not None:
                tenant_slug = t.slug
        except Exception:
            pass

        # 4) Resolver pipeline del catalogo del tenant
        pipelines = get_tenant_pipelines(tenant_slug)
        if pipeline_id not in pipelines:
            self.log.append(Event(
                kind="ScheduledPipelineFailed",
                entity_id=f"pipeline://{pipeline_id}",
                tenant_id=tenant_id,
                actor_id="orchestrator",
                payload={"error": f"pipeline desconocido: {pipeline_id}"},
                correlation_id=correlation_id,
                command_id=command_id,
            ))
            return {"status": "UNKNOWN_PIPELINE", "pipeline_id": pipeline_id}

        # 5) Validar catalogo y ejecutar via runner
        assert_tenant_catalog_valid(tenant_slug, executor.registry)
        runner = PipelineRunner(
            executor=executor, llm=self.llm, tenant_slug=tenant_slug
        )
        return runner.run(
            pipeline_id=pipeline_id,
            tenant_id=tenant_id,
            params=params or {},
            correlation_id=correlation_id,
            command_id=command_id,
            tenant_slug=tenant_slug,
        )