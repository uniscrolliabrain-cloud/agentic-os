"""Entidades de ejemplo para tests y demos — NO son kernel ni tenant."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field, field_validator

from ...kernel.ontology.domain_models import (
    BaseDomainModel,
    register_entity_types,
)


class Lead(BaseDomainModel):
    kind: Literal["marketing.lead"] = "marketing.lead"
    name: str
    email: str
    source: str = "organic"
    status: str = "new"

    @field_validator("email")
    @classmethod
    def _validate_email(cls, v: str) -> str:
        if "@" not in v or " " in v:
            raise ValueError("email invalido")
        return v


class Proposal(BaseDomainModel):
    kind: Literal["marketing.proposal"] = "marketing.proposal"
    lead_id: str
    amount: float = Field(ge=0)
    status: str = "draft"

    @field_validator("lead_id")
    @classmethod
    def _lead_id_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("lead_id obligatorio")
        return v


class Brand(BaseDomainModel):
    kind: Literal["marketing.brand"] = "marketing.brand"
    name: str
    website: str | None = None


class Campaign(BaseDomainModel):
    kind: Literal["marketing.campaign"] = "marketing.campaign"
    name: str
    brand_id: str
    budget: float = Field(ge=0)

    @field_validator("brand_id")
    @classmethod
    def _brand_id_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("brand_id obligatorio")
        return v


class BlogPost(BaseDomainModel):
    kind: Literal["content.blog_post"] = "content.blog_post"
    title: str
    body: str

    @field_validator("title")
    @classmethod
    def _title_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("title obligatorio")
        return v


class CoachingClient(BaseDomainModel):
    kind: Literal["coaching.client"] = "coaching.client"
    name: str
    email: str

    @field_validator("email")
    @classmethod
    def _validate_email(cls, v: str) -> str:
        if "@" not in v or " " in v:
            raise ValueError("email invalido")
        return v


class SessionNote(BaseDomainModel):
    kind: Literal["coaching.session_note"] = "coaching.session_note"
    client_id: str
    notes: str

    @field_validator("client_id")
    @classmethod
    def _client_id_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("client_id obligatorio")
        return v


class TherapyClient(BaseDomainModel):
    kind: Literal["therapy.client"] = "therapy.client"
    name: str
    specialty: str


class Appointment(BaseDomainModel):
    kind: Literal["therapy.appointment"] = "therapy.appointment"
    client_id: str
    scheduled_at: datetime
    status: str = "pending"

    @field_validator("client_id")
    @classmethod
    def _client_id_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("client_id obligatorio")
        return v


DEMO_ENTITIES = (Lead, Proposal, Brand, Campaign, BlogPost,
                 CoachingClient, SessionNote, TherapyClient, Appointment)


def register_demo_entities() -> None:
    """Registra las 9 en ENTITY_TYPE_REGISTRY. Solo tests/demos lo llaman."""
    register_entity_types(*DEMO_ENTITIES)
