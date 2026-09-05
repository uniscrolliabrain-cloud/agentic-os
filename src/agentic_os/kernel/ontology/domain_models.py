"""Entidades de dominio tipadas.

Bloque A - domain_models.py
Implementa la base de entidades de dominio con validacion estricta.

Codigo de referencia basado en ontology_prompt_finalv3.md (PARTE VI, ~1985-2138).
Bugs corregidos segun plan_implementacion_clinev2.md.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ..types.ids import new_id
from ..types.time import now_utc


class BaseDomainModel(BaseModel):
    """Base comun para entidades y contratos de dominio.

    - frozen=True: inmutabilidad garantizada.
    - extra='forbid': rechaza campos inesperados (evita typos de API).
    - validate_assignment=True: valida siempre que se asigne un campo.
    - use_enum_values=True: almacena valores, no wrappers.
    - Tenant_id obligatorio: nada de entidades huerfanas.
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

    @model_validator(mode="before")
    @classmethod
    def _default_entity_type(cls, data: Any) -> Any:
        """Propaga kind -> entity_type antes de la validacion (para subclases con kind fijo)."""
        if isinstance(data, dict):
            kind = data.get("kind")
            # Si entity_type no se prove, propaga kind como entity_type
            if "entity_type" not in data and kind is not None:
                data["entity_type"] = kind
            elif "entity_type" not in data:
                # Intenta obtener kind del modelo (valor por defecto)
                try:
                    kind_field = cls.model_fields.get("kind")
                    if kind_field and kind_field.default:
                        data["entity_type"] = kind_field.default
                except Exception:
                    pass
        return data

    @field_validator("tenant_id")
    @classmethod
    def _tenant_id_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("tenant_id es obligatorio (invariante multi-tenant)")
        return v

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
        """Sincroniza entity_type con kind si kind esta definido."""
        kind_val = getattr(self, "kind", None)
        if kind_val is not None and not self.entity_type:
            object.__setattr__(self, "entity_type", kind_val)
        return self


# Alias de compatibilidad: DomainEntity es el nombre canonico solicitado.
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
            raise ValueError("brand_id obligatorio")
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


# --- A5: Registro de tipos de entidad ---

ENTITY_TYPE_REGISTRY: dict[str, type[BaseDomainModel]] = {
    cls.model_fields["kind"].default: cls
    for cls in (Lead, Proposal, Brand, Campaign, BlogPost, CoachingClient, SessionNote, TherapyClient, Appointment)
}


class UnknownEntityTypeError(KeyError):
    """Se pidio un kind no registrado en ENTITY_TYPE_REGISTRY (fail-closed)."""


def entity_from_payload(kind: str, data: dict) -> BaseDomainModel:
    """Construye una entidad tipada a partir de kind + payload (fail-closed).

    Lanza UnknownEntityTypeError si kind no esta registrado y ValidationError
    si el payload no valida contra la clase correspondiente. Nunca devuelve
    un dict suelto ni acepta tipos implicitos.
    """
    cls = ENTITY_TYPE_REGISTRY.get(kind)
    if cls is None:
        raise UnknownEntityTypeError(
            f"entity_type '{kind}' no registrado en ENTITY_TYPE_REGISTRY"
        )
    return cls(**data)


def validate_registry_integrity() -> None:
    """Verifica que cada clave del registro coincide con el Literal kind de su clase."""
    for key, cls in ENTITY_TYPE_REGISTRY.items():
        kind_field = cls.model_fields.get("kind")
        default_kind = getattr(kind_field, "default", None) if kind_field else None
        if kind_field is None or default_kind != key:
            raise ValueError(
                f"ENTITY_TYPE_REGISTRY corrupto: clave '{key}' no coincide "
                f"con el kind de {cls.__name__}"
            )