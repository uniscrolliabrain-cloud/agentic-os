"""Entidades del dominio `agencia` (FASE 1 - PLAN_AGENCIA_TENANT.md)."""
from __future__ import annotations

import re
from datetime import datetime
from typing import Dict, List, Literal, Optional
from urllib.parse import urlparse

from pydantic import Field, field_validator, model_validator

from ...kernel.ontology.domain_models import BaseDomainModel
from ...kernel.types import KernelModel

LeadStatus = Literal["capturado", "validado", "contactado", "cita", "deal", "cerrado", "invalido"]
DealStage = Literal["nuevo", "calificado", "propuesta", "ganado", "perdido", "cerrado"]
ServiceKind = Literal["web_design", "web_redesign", "community_management", "ai_services", "agentic_services", "gmb_update", "seo"]

AGENCIA_ENTITY_KINDS = frozenset({
    "agencia.client", "agencia.lead", "agencia.appointment", "agencia.deal",
    "agencia.quote", "agencia.audit_report", "agencia.social_post",
})

_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,62}[a-z0-9]?$")
_PHONE_RE = re.compile(r"^\+?[0-9][0-9()\-\s]{5,}$")


def _validate_email(v: str) -> str:
    if not v or "@" not in v or " " in v:
        raise ValueError("email invalido")
    return v


def _validate_phone(v: str) -> str:
    v = v.strip()
    if not v or not _PHONE_RE.match(v) or len(re.sub(r"\D", "", v)) < 7:
        raise ValueError("phone invalido (formato E.164 basico)")
    return v


def _validate_http_url(v: str) -> str:
    v = v.strip()
    parsed = urlparse(v)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError("url invalida: debe ser http(s)://...")
    return v


def _validate_not_empty(v: str, field: str) -> str:
    if not v or not v.strip():
        raise ValueError(f"{field} obligatorio")
    return v.strip()


class ServiceItem(KernelModel):
    service: ServiceKind
    description: str = Field(..., min_length=1)
    price: float = Field(..., ge=0)
    unit: str = ""


class AgencyClient(BaseDomainModel):
    kind: Literal["agencia.client"] = "agencia.client"
    name: str
    slug: str
    timezone: str = "Europe/Madrid"
    providers: List[str] = Field(default_factory=list)

    @field_validator("name")
    @classmethod
    def _name_valid(cls, v: str) -> str:
        return _validate_not_empty(v, "name")

    @field_validator("slug")
    @classmethod
    def _slug_valid(cls, v: str) -> str:
        v = (v or "").strip().lower()
        if not _SLUG_RE.match(v) or ".." in v or "/" in v or "\\" in v:
            raise ValueError("slug invalido (solo minusculas, numeros, - y _)")
        return v

    @field_validator("providers")
    @classmethod
    def _providers_valid(cls, v: List[str]) -> List[str]:
        seen: List[str] = []
        for p in v:
            p = (p or "").strip()
            if not p:
                raise ValueError("providers no puede contener cadenas vacias")
            if p in seen:
                raise ValueError(f"provider duplicado: {p}")
            seen.append(p)
        return seen


class AgencyLead(BaseDomainModel):
    kind: Literal["agencia.lead"] = "agencia.lead"
    client_id: str
    name: str
    email: str
    phone: str
    source: str
    status: LeadStatus = "capturado"

    @field_validator("client_id")
    @classmethod
    def _client_valid(cls, v: str) -> str:
        return _validate_not_empty(v, "client_id")

    @field_validator("name")
    @classmethod
    def _name_valid(cls, v: str) -> str:
        return _validate_not_empty(v, "name")

    @field_validator("email")
    @classmethod
    def _email_valid(cls, v: str) -> str:
        return _validate_email((v or "").strip())

    @field_validator("phone")
    @classmethod
    def _phone_valid(cls, v: str) -> str:
        return _validate_phone(v)

    @field_validator("source")
    @classmethod
    def _source_valid(cls, v: str) -> str:
        return _validate_not_empty(v, "source")


class AgencyAppointment(BaseDomainModel):
    kind: Literal["agencia.appointment"] = "agencia.appointment"
    client_id: str
    lead_id: str
    calendar_provider: str = "google"
    scheduled_at: datetime
    external_id: Optional[str] = None

    @field_validator("client_id")
    @classmethod
    def _client_valid(cls, v: str) -> str:
        return _validate_not_empty(v, "client_id")

    @field_validator("lead_id")
    @classmethod
    def _lead_valid(cls, v: str) -> str:
        return _validate_not_empty(v, "lead_id")

    @field_validator("scheduled_at")
    @classmethod
    def _scheduled_aware(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("scheduled_at debe llevar timezone (UTC)")
        return v


class AgencyDeal(BaseDomainModel):
    kind: Literal["agencia.deal"] = "agencia.deal"
    client_id: str
    lead_id: str
    quote_id: Optional[str] = None
    stage: DealStage = "nuevo"
    total: float = Field(..., ge=0)
    stripe_link: Optional[str] = None
    payment_status: str = "pending"

    @field_validator("client_id")
    @classmethod
    def _client_valid(cls, v: str) -> str:
        return _validate_not_empty(v, "client_id")

    @field_validator("lead_id")
    @classmethod
    def _lead_valid(cls, v: str) -> str:
        return _validate_not_empty(v, "lead_id")

    @field_validator("stripe_link")
    @classmethod
    def _stripe_link_valid(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return None
        return _validate_http_url(v)


class ServiceQuote(BaseDomainModel):
    kind: Literal["agencia.quote"] = "agencia.quote"
    client_id: str
    lead_id: Optional[str] = None
    service_items: List[ServiceItem] = Field(default_factory=list)
    total: Optional[float] = None
    currency: str = "EUR"
    stripe_link: Optional[str] = None

    @field_validator("client_id")
    @classmethod
    def _client_valid(cls, v: str) -> str:
        return _validate_not_empty(v, "client_id")

    @field_validator("service_items")
    @classmethod
    def _items_not_empty(cls, v: List[ServiceItem]) -> List[ServiceItem]:
        if not v:
            raise ValueError("service_items debe contener al menos un item")
        return v

    @field_validator("stripe_link")
    @classmethod
    def _stripe_link_valid(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return None
        return _validate_http_url(v)

    @model_validator(mode="after")
    def _compute_total(self) -> "ServiceQuote":
        computed = round(sum(i.price for i in self.service_items), 2)
        if self.total is None:
            object.__setattr__(self, "total", computed)
        elif abs(self.total - computed) > 0.005:
            raise ValueError(f"total ({self.total}) no coincide con la suma de los items ({computed})")
        return self


class AuditReport(BaseDomainModel):
    kind: Literal["agencia.audit_report"] = "agencia.audit_report"
    client_id: str
    url: str
    checklist: Dict[str, bool] = Field(default_factory=dict)
    score: float = Field(..., ge=0, le=100)
    recommendations: List[str] = Field(default_factory=list)

    @field_validator("client_id")
    @classmethod
    def _client_valid(cls, v: str) -> str:
        return _validate_not_empty(v, "client_id")

    @field_validator("url")
    @classmethod
    def _url_valid(cls, v: str) -> str:
        return _validate_http_url(v)

    @field_validator("checklist")
    @classmethod
    def _checklist_valid(cls, v: Dict[str, bool]) -> Dict[str, bool]:
        for key in v:
            if not key.strip():
                raise ValueError("checklist no puede contener claves vacias")
        return v


class SocialPost(BaseDomainModel):
    kind: Literal["agencia.social_post"] = "agencia.social_post"
    channel: Literal["meta", "linkedin", "tiktok"] = "meta"
    content: str = Field(min_length=1)
    source_asset: str = ""
    scheduled_at: Optional[datetime] = None


__all__ = [
    "AGENCIA_ENTITY_KINDS", "LeadStatus", "DealStage", "ServiceKind", "ServiceItem",
    "AgencyClient", "AgencyLead", "AgencyAppointment", "AgencyDeal",
    "ServiceQuote", "AuditReport", "SocialPost",
]