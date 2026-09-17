"""Pipelines canonicos del tenant bor-agencia - modelos Pydantic strict."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


TENANT_SLUG = "bor-agencia"


class PipelineStep(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    tool: str = Field(min_length=1)
    description: str = ""
    output_key: str = Field(default="output", min_length=1)
    optional: bool = False

    @field_validator("tool")
    @classmethod
    def _tool_nonblank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("tool no puede estar en blanco")
        return v.strip()


class AgencyPipeline(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(min_length=1)
    name: str
    tenant: Literal["bor-agencia"] = TENANT_SLUG
    purpose: str = ""
    steps: list[PipelineStep] = Field(default_factory=list)
    requires_approval: bool = False
    enabled: bool = True

    @field_validator("steps")
    @classmethod
    def _steps_no_vacios(cls, v: list[PipelineStep]) -> list[PipelineStep]:
        if not v:
            raise ValueError("un pipeline debe declarar al menos un step")
        return v


PIPELINE_LEADS_TO_DRAFT = AgencyPipeline(
    id="leads_to_draft",
    name="Leads a borradores",
    purpose=(
        "Lee leads (CSV/JSON) de la cache Drive del cliente, valida cada "
        "lead como AgencyLead y crea un borrador de email por lead. "
        "NUNCA envia."
    ),
    steps=[
        PipelineStep(tool="drive_list_files", output_key="files"),
        PipelineStep(tool="drive_read_file", output_key="content"),
        PipelineStep(tool="gmail_create_draft", output_key="drafts_created"),
    ],
)

PIPELINE_INBOX_WATCHER = AgencyPipeline(
    id="inbox_watcher",
    name="Vigia de bandeja",
    purpose=(
        "Lista unread, clasifica (lead/soporte/spam) y crea borradores de "
        "respuesta para los leads. NUNCA envia."
    ),
    steps=[
        PipelineStep(tool="gmail_list_unread", output_key="emails"),
        PipelineStep(tool="gmail_create_draft", output_key="drafts_created"),
    ],
)

PIPELINE_DAILY_SOCIAL = AgencyPipeline(
    id="daily_social",
    name="Publicacion social diaria",
    purpose=(
        "Toma contenido de la cache Drive, genera copy con el LLM y publica "
        "en Meta (SIMULADO). Guarda artefacto por fecha."
    ),
    requires_approval=True,
    steps=[
        PipelineStep(tool="drive_list_files", output_key="files"),
        PipelineStep(tool="drive_read_file", output_key="content"),
        PipelineStep(tool="meta_post_publish", output_key="publish"),
    ],
)

PIPELINES: dict[str, AgencyPipeline] = {
    p.id: p
    for p in (
        PIPELINE_LEADS_TO_DRAFT,
        PIPELINE_INBOX_WATCHER,
        PIPELINE_DAILY_SOCIAL,
    )
}

__all__ = [
    "TENANT_SLUG",
    "PipelineStep",
    "AgencyPipeline",
    "PIPELINE_LEADS_TO_DRAFT",
    "PIPELINE_INBOX_WATCHER",
    "PIPELINE_DAILY_SOCIAL",
    "PIPELINES",
]