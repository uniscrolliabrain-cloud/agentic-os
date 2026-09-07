"""Entidades de dominio tipadas.

Bloque A — domain_models.py
Implementa la base de entidades de dominio con validación estricta.

Código de referencia basado en ontology_prompt_finalv3.md (PARTE VI, ~1985-2138).
Bugs corregidos según plan_implementacion_clinev2.md.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ..types.ids import new_id
from ..types.time import now_utc


class BaseDomainModel(BaseModel):
    """Base común para entidades y contratos de dominio.

    - frozen=True: inmutabilidad garantizada.
    - extra='forbid': rechaza campos inesperados (evita typos de API).
    - validate_assignment=True: valida siempre que se asigne un campo.
    - use_enum_values=True: almacena valores, no wrappers.
    - Tenant_id obligatorio: nada de entidades huérfanas.
    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        validate_assignment=True,
        use_enum_values=True,
    )

            id: str = Field(default_factory=new_id)
    tenant_id: str
    entity_type: str
    created_at: datetime = Field(default_factory=now_utc)
    version: int = Field(default=0)

    @field_validator("tenant_id")
    @classmethod
    def _tenant_id_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("tenant_id es obligatorio (invariante multi-tenant)")
        return v

    @model_validator(mode="before")
    @classmethod
    def _default_entity_type(cls, data: Any) -> Any:
        """Si entity_type no se prove, propaga kind (si existe) o deja campo pendiente."""
        if isinstance(data, dict):
            kind = data.get("kind")
            if "entity_type" not in data or not data.get("entity_type"):
                if kind:
                    data["entity_type"] = kind
                elif "entity_type" not in data:
                    data.pop("entity_type", None)
        return data

    @field_validator("entity_type")
    @classmethod
    def _entity_type_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("entity_type es obligatorio (discriminador de Union)")
        return v

    @field_validator("version")
    @classmethod
    def _version_no_negativa(cls, v: int) -> int:
        if v < 0:
            raise ValueError("version no puede ser negativa")
        return v

    @model_validator(mode="after")
    def _sync_entity_type_from_kind(self):
        """Sincroniza entity_type con kind si kind está definido (subclases)."""
        kind_val = getattr(self, "kind", None)
        if kind_val is not None and not self.entity_type:
            object.__setattr__(self, "entity_type", kind_val)
        return self


# Alias de compatibilidad: DomainEntity es el nombre canónico solicitado.
DomainEntity = BaseDomainModel


# --- A2: Lead y Proposal ---

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
            raise ValueError("email inválido")
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
            raise ValueError("lead_id es obligatorio")
        return v


# --- A3: Brand y Campaign ---

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
            raise ValueError("brand_id es obligatorio")
        return v


# --- A4: BlogPost + CoachingClient, SessionNote + TherapyClient, Appointment ---

class BlogPost(BaseDomainModel):
    kind: Literal["content.blog_post"] = "content.blog_post"
    title: str
    body: str

    @field_validator("title")
    @classmethod
    def _title_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("title es obligatorio")
        return v


class CoachingClient(BaseDomainModel):
    kind: Literal["coaching.client"] = "coaching.client"
    name: str
    email: str

    @field_validator("email")
    @classmethod
    def _validate_email(cls, v: str) -> str:
        if "@" not in v or " " in v:
            raise ValueError("email inválido")
        return v


class SessionNote(BaseDomainModel):
    kind: Literal["coaching.session_note"] = "coaching.session_note"
    client_id: str
    notes: str

    @field_validator("client_id")
    @classmethod
    def _client_id_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("client_id es obligatorio")
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
            raise ValueError("client_id es obligatorio")
        return v
