from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

class SkillStep(BaseModel):
    """Paso determinista del SOP."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    order: int = Field(ge=0)
    name: str
    description: str = ""
    tool: str = Field(description="capability/tool ej. gmail_send")
    requires: Optional[str] = Field(default=None, description="campo que debe venir del paso anterior")
    validation: Optional[str] = Field(default=None, description="regla ej. email_valido, url_valida")
    output_key: str = Field(default="output", description="donde guardar el output en el contexto")
    timeout_seconds: int = Field(default=60, gt=0)

    @field_validator("name", "tool")
    @classmethod
    def _nonblank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("campo obligatorio vacio")
        return v.strip()

class Skill(BaseModel):
    """Skill = SOP formal con input/output schema + pasos validados."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    description: str
    category: str = Field(default="general", description="research, communication, automation...")
    requires_tool: str
    steps: List[SkillStep] = Field(default_factory=list)
    role_required: str = Field(default="operator")
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    output_schema: Dict[str, Any] = Field(default_factory=dict)
    preconditions: List[str] = Field(default_factory=list)
    postconditions: List[str] = Field(default_factory=list)
    version: str = Field(default="1.0")

    @field_validator("steps")
    @classmethod
    def _steps_ordered(cls, v: List[SkillStep]) -> List[SkillStep]:
        orders = [s.order for s in v]
        if orders != sorted(orders):
            raise ValueError("Skill steps deben estar ordenados por order")
        if len(set(orders)) != len(orders):
            raise ValueError("order duplicado en SkillStep")
        return v

    def validate_input(self, payload: Dict[str, Any]) -> None:
        # validacion basica de required keys si input_schema tiene required
        required = self.input_schema.get("required", [])
        for key in required:
            if key not in payload:
                raise ValueError(f"Skill {self.name!r} requiere input {key!r}")

    def tool_chain(self) -> List[str]:
        return [s.tool for s in self.steps]
