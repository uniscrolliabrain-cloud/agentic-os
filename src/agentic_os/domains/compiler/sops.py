"""SOPs del tenant agentic-compiler - modelos Pydantic."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


TENANT_SLUG = "agentic-compiler"
SopRole = Literal["director", "operator", "auditor"]


class SOP(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    tenant: Literal["agentic-compiler"] = TENANT_SLUG
    version: str = "1.0"
    trigger: str = Field(min_length=1)
    pipeline_id: str = Field(min_length=1)
    requires_role: SopRole = "director"
    requires_approval: bool = False
    preconditions: list[str] = Field(default_factory=list)
    postconditions: list[str] = Field(default_factory=list)

    @field_validator("id")
    @classmethod
    def _id_namespaced(cls, v: str) -> str:
        if not v.startswith(f"{TENANT_SLUG}."):
            raise ValueError(f"SOP.id debe empezar por '{TENANT_SLUG}.'")
        return v


SOP_BLUEPRINT_FROM_IDEA = SOP(
    id="agentic-compiler.blueprint_from_idea",
    name="Idea a blueprint",
    trigger="manual",
    pipeline_id="blueprint_from_idea",
    requires_role="director",
    requires_approval=False,
    preconditions=["tenant registrado con repo.file.read permitido"],
    postconditions=["TenantBlueprint(status='proposed') en la conversacion del tenant"],
)

SOP_COMPILE_TENANT = SOP(
    id="agentic-compiler.compile_tenant",
    name="Compilar tenant (Gate 1 ya aprobado)",
    trigger="manual",
    pipeline_id="compile_tenant",
    requires_role="director",
    requires_approval=True,
    preconditions=["blueprint.status == 'approved' (Gate 1 resuelto)"],
    postconditions=[
        "rama agentic-os-roo con el codigo generado",
        "PR abierto, pendiente de merge humano (Gate 2)",
    ],
)

SOPS: dict[str, SOP] = {
    s.id: s for s in (SOP_BLUEPRINT_FROM_IDEA, SOP_COMPILE_TENANT)
}

__all__ = [
    "TENANT_SLUG",
    "SopRole",
    "SOP",
    "SOP_BLUEPRINT_FROM_IDEA",
    "SOP_COMPILE_TENANT",
    "SOPS",
]