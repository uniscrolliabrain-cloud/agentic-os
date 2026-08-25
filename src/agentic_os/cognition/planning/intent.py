from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from ...kernel.types.ids import new_id


class Intent(BaseModel):
    """
    Lo que un rol con permiso 'propose_intent' (ej. Gemini como 'director')
    propone que ocurra. NO es una acción ejecutada: todavía tiene que pasar
    por el policy engine (policy/evaluator.py) antes de convertirse en un
    Event real dentro del world log.
    """
    model_config = ConfigDict(frozen=True)
    id: str = Field(default_factory=new_id)
    goal: str  # qué quiere lograr, en una frase (ej. "responder al usuario", "crear una cita")
    kind: str  # tipo de acción propuesta, ej. "send_email", "create_appointment", "reply_to_user"
    entity_id: str = "n/a"  # sobre qué entidad actúa, si aplica
    payload: str = ""  # detalles adicionales en texto libre por ahora (se estructurará más adelante)
    rationale: str = ""  # por qué Gemini propone esto — queda en el log, auditable
    reply_to_user: Optional[str] = None  # texto en lenguaje natural para mostrar en el chat
    confidence: Optional[float] = None
