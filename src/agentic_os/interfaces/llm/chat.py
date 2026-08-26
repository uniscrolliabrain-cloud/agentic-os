"""Asistente frontal (PR) de AGENTE OS.

Es la capa con la que habla el usuario: rápida, conversacional y con knowledge
base. El orquestador real (Intent -> Policy -> Executor -> EventLog) corre en
segundo plano en el backend; aquí NO se propone ni se ejecuta nada, solo se
conversa de forma natural apoyándose en la knowledge base local.
"""
from __future__ import annotations

from typing import List, Optional

from .knowledge import KnowledgeBase
from .provider import BaseLLMProvider, GeminiProvider, MockLLMProvider

PERSONA_SYSTEM = """
Eres AGENTE OS, el asistente frontal de una plataforma de inteligencia agéntica
para empresas.

Reglas:
- Responde de forma natural y concisa en el idioma del usuario.
- Usa la base de conocimiento que se te entrega para responder con datos reales
  de la plataforma (clientes, arquitectura, skills, herramientas, invariantes).
- NO actúes como si ejecutaras acciones. Si el usuario pide algo que requiere
  una acción (enviar correo, crear reunión, etc.), reconócelo amablemente y
  dile que lo dejarás en manos del equipo de operaciones (el director) que lo
  procesará en segundo plano.
- No inventes datos que no estén en la base de conocimiento o en la conversación.
"""


class FrontAssistant:
    """Asistente de cara al usuario: persona PR + knowledge base, respuesta rápida."""

    def __init__(
        self,
        model_name: str = "gemini-3.6-flash",
        api_key: Optional[str] = None,
        temperature: Optional[float] = None,
        knowledge_dir=None,
    ):
        self.kb = KnowledgeBase(directory=knowledge_dir)
        if api_key:
            self.provider: BaseLLMProvider = GeminiProvider(
                api_key=api_key, model=model_name, temperature=temperature
            )
        else:
            self.provider = MockLLMProvider(
                default_response=(
                    "Hola, soy el asistente de AGENTE OS (modo mock). "
                    "Configura GEMINI_API_KEY para conversar con la knowledge base."
                )
            )

    def answer(self, user_message: str) -> str:
        """Genera una respuesta rápida y natural usando la knowledge base."""
        snippets = self.kb.retrieve(user_message)
        if snippets:
            context = "\n\n".join(
                f"[{s['title']}]\n{s['text'][:2200].strip()}" for s in snippets
            )
            system = PERSONA_SYSTEM + "\n\nBASE DE CONOCIMIENTO (úsala si aplica):\n" + context
        else:
            system = PERSONA_SYSTEM
        return self.provider.generate(prompt=user_message, system_instruction=system)