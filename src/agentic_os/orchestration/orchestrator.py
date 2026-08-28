from __future__ import annotations

from ..kernel.world.replay import replay
from ..kernel.world.events import Event, EventLog
from ..cognition.roles.library import LIBRARY
from ..cognition.planning.intent import Intent
from ..interfaces.llm.provider import BaseLLMProvider


class Orchestrator:
    def __init__(self, log: EventLog, llm: BaseLLMProvider):
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
