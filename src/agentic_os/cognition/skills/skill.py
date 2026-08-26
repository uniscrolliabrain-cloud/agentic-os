from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class SkillStep(BaseModel):
    """Un paso dentro del SOP (procedimiento operativo estándar) de un skill.

    Cada paso es determinista: define qué tool llama y cómo valida la salida.
    """

    model_config = ConfigDict(frozen=True)

    order: int
    name: str
    tool: str  # capability/tool a la que llama (ej. "gmail_send")
    requires: Optional[str] = None  # campo que debe venir del paso anterior
    validation: Optional[str] = None  # regla opcional (ej. "email_valido")


class Skill(BaseModel):
    """Un Skill = un SOP formal: taxonomía + pipeline de pasos + permisos.

    El LLM NUNCA ejecuta: solo propone una Intent con el skill y los
    parámetros. El sistema instancia el Skill y ejecuta sus pasos de forma
    determinista, validando cada paso contra las leyes Pydantic.
    """

    model_config = ConfigDict(frozen=True)

    name: str
    description: str
    requires_tool: str  # capability principal (para compatibilidad)
    steps: List[SkillStep] = Field(default_factory=list)
    role_required: str = "operator"  # rol mínimo que puede ejecutar el skill
    input_schema: Dict[str, Any] = Field(default_factory=dict)  # esquema de entrada
    output_schema: Dict[str, Any] = Field(default_factory=dict)  # esquema de salida
