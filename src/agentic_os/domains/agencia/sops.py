"""SOPs del tenant bor-agencia - modelos Pydantic strict."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


TENANT_SLUG = "bor-agencia"
SopRole = Literal["director", "operator", "auditor"]


class SOP(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    tenant: Literal["bor-agencia"] = TENANT_SLUG
    version: str = "1.0"
    trigger: str = Field(min_length=1)
    pipeline_id: str = Field(min_length=1)
    requires_role: SopRole = "operator"
    requires_approval: bool = False
    preconditions: list[str] = Field(default_factory=list)
    postconditions: list[str] = Field(default_factory=list)

    @field_validator("id")
    @classmethod
    def _id_namespaced(cls, v: str) -> str:
        if not v.startswith(f"{TENANT_SLUG}."):
            raise ValueError(f"SOP.id debe empezar por '{TENANT_SLUG}.'")
        return v


SOP_LEADS_TO_DRAFT = SOP(
    id="bor-agencia.leads_to_draft",
    name="Leads a borradores",
    trigger="manual",
    pipeline_id="leads_to_draft",
    requires_role="operator",
    preconditions=["drive cache con ficheros en leads/<tenant>"],
    postconditions=[
        "un draft JSON por lead valido en data/tenants/<tenant>/drafts/",
        "entidades AgencyLead en el WorldState (via entity_created)",
    ],
)

SOP_INBOX_WATCHER = SOP(
    id="bor-agencia.inbox_watcher",
    name="Vigia de bandeja",
    trigger="cron: */30 * * * *",
    pipeline_id="inbox_watcher",
    requires_role="operator",
    postconditions=["drafts en data/tenants/<tenant>/drafts/ (nunca envia)"],
)

SOP_DAILY_SOCIAL = SOP(
    id="bor-agencia.daily_social",
    name="Publicacion social diaria",
    trigger="cron: 0 9 * * *",
    pipeline_id="daily_social",
    requires_role="director",
    requires_approval=True,
    preconditions=["drive cache con content_to_post/<tenant>"],
    postconditions=["artefacto en data/tenants/<tenant>/artifacts/<date>/"],
)

SOPS: dict[str, SOP] = {
    s.id: s for s in (SOP_LEADS_TO_DRAFT, SOP_INBOX_WATCHER, SOP_DAILY_SOCIAL)
}

__all__ = [
    "TENANT_SLUG",
    "SopRole",
    "SOP",
    "SOP_LEADS_TO_DRAFT",
    "SOP_INBOX_WATCHER",
    "SOP_DAILY_SOCIAL",
    "SOPS",
]