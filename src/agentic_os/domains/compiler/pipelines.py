"""Pipelines canonicos del tenant agentic-compiler - modelos Pydantic."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


TENANT_SLUG = "agentic-compiler"


class CompilerStep(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    tool: str = Field(min_length=1)
    description: str = ""
    output_key: str = Field(default="output", min_length=1)


class CompilerPipeline(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(min_length=1)
    name: str
    tenant: Literal["agentic-compiler"] = TENANT_SLUG
    purpose: str = ""
    mode: Literal["plan", "act"] = "plan"
    requires_gate: Literal["gate_1", "gate_2", ""] = ""
    steps: list[CompilerStep] = Field(default_factory=list)
    enabled: bool = False

    @field_validator("steps")
    @classmethod
    def _no_empty(cls, v: list[CompilerStep]) -> list[CompilerStep]:
        if not v:
            raise ValueError("un pipeline debe declarar al menos un step")
        return v


PIPELINE_BLUEPRINT_FROM_IDEA = CompilerPipeline(
    id="blueprint_from_idea",
    name="Idea a blueprint",
    purpose=(
        "Lee el repo (solo lectura) y propone un TenantBlueprint en modo PLAN. "
        "NUNCA escribe."
    ),
    mode="plan",
    requires_gate="gate_1",
    steps=[
        CompilerStep(tool="repo_search", output_key="matches"),
        CompilerStep(tool="repo_file_read", output_key="context"),
    ],
)

PIPELINE_COMPILE_TENANT = CompilerPipeline(
    id="compile_tenant",
    name="Blueprint a tenant vivo",
    purpose=(
        "Genera el andamiaje del tenant nuevo en la rama agentic-os-roo, "
        "corre CI, abre PR. Requiere Gate 2 humano antes de merge."
    ),
    mode="act",
    requires_gate="gate_2",
    steps=[
        CompilerStep(tool="repo_file_write", output_key="plan_written"),
        CompilerStep(tool="git_branch_create", output_key="branch"),
        CompilerStep(tool="git_commit", output_key="commit"),
        CompilerStep(tool="ci_pytest_run", output_key="ci_result"),
        CompilerStep(tool="git_push", output_key="pushed"),
        CompilerStep(tool="git_pr_create", output_key="pr"),
    ],
)

PIPELINES: dict[str, CompilerPipeline] = {
    p.id: p for p in (PIPELINE_BLUEPRINT_FROM_IDEA, PIPELINE_COMPILE_TENANT)
}

__all__ = [
    "TENANT_SLUG",
    "CompilerStep",
    "CompilerPipeline",
    "PIPELINE_BLUEPRINT_FROM_IDEA",
    "PIPELINE_COMPILE_TENANT",
    "PIPELINES",
]