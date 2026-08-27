from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------- Command ---
class Command(BaseModel):
    """La unidad canónica que cruza el kernel. Un agente NO puede construir
    un Command libremente: lo construye el orquestador a partir de una microacción
    validada. Contiene el propósito, no credenciales."""

    model_config = ConfigDict(frozen=True)

    capability: str          # p.ej. "crm.contact.create"
    params: Dict[str, Any] = Field(default_factory=dict)
    workspace_id: Optional[str] = None
    tenant_id: Optional[str] = None
    actor_id: Optional[str] = None
    execution_id: Optional[str] = None   # idempotencia interna
    correlation_id: Optional[str] = None
    dry_run: bool = False


class CommandResult(BaseModel):
    """Resultado normalizado de ejecutar un Command."""

    model_config = ConfigDict(frozen=True)

    ok: bool
    output: Any = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    execution_id: Optional[str] = None
    connector_id: Optional[str] = None
    provider: Optional[str] = None
    capability: Optional[str] = None
    duration_ms: int = 0
    dry_run: bool = False
    preview: Optional[Dict[str, Any]] = None   # lo que PASARÍA (dry_run)


# ------------------------------------------------------------------ Health ---
class HealthStatus(str):
    """Estados de salud de un connector: HEALTHY, DEGRADED, AUTH_REQUIRED,
    RATE_LIMITED, UNAVAILABLE, MISCONFIGURED, DISABLED."""

    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    AUTH_REQUIRED = "AUTH_REQUIRED"
    RATE_LIMITED = "RATE_LIMITED"
    UNAVAILABLE = "UNAVAILABLE"
    MISCONFIGURED = "MISCONFIGURED"
    DISABLED = "DISABLED"


class HealthStatusModel(BaseModel):
    status: str
    provider: Optional[str] = None
    detail: str = ""
    last_checked_at: datetime = Field(default_factory=_utcnow)


class CredentialStatus(BaseModel):
    status: str            # "valid" | "expired" | "missing" | "revoked" | "invalid"
    provider: Optional[str] = None
    detail: str = ""
    expires_at: Optional[datetime] = None


# -------------------------------------------------------------- Pagination ---
class Page(BaseModel, Generic[T]):
    items: List[T] = Field(default_factory=list)
    next_cursor: Optional[str] = None
    has_more: bool = False


# ----------------------------------------------------------------- Artifact --
class Artifact(BaseModel):
    """Fichero/media producido por un connector. Se guarda referencias, no binario."""

    model_config = ConfigDict(frozen=True)

    artifact_id: str
    type: str                    # "image" | "document" | "audio" | "video" | ...
    mime_type: str
    name: str
    storage_reference: str
    size: int = 0
    checksum: Optional[str] = None
    provider: Optional[str] = None
    external_id: Optional[str] = None
    created_at: datetime = Field(default_factory=_utcnow)


# ---------------------------------------------------------------- Risk ---
class RiskClass(str):
    READ_ONLY = "READ_ONLY"
    LOW_RISK_WRITE = "LOW_RISK_WRITE"
    EXTERNAL_COMMUNICATION = "EXTERNAL_COMMUNICATION"
    FINANCIAL = "FINANCIAL"
    DESTRUCTIVE = "DESTRUCTIVE"
    SECURITY_SENSITIVE = "SECURITY_SENSITIVE"


RISK_BY_CAPABILITY_PREFIX: Dict[str, str] = {
    "email.message.send": RiskClass.EXTERNAL_COMMUNICATION,
    "communication.sms.send": RiskClass.EXTERNAL_COMMUNICATION,
    "social.post.publish": RiskClass.EXTERNAL_COMMUNICATION,
    "finance.": RiskClass.FINANCIAL,
    "payment.": RiskClass.FINANCIAL,
    "database.record.delete": RiskClass.DESTRUCTIVE,
    "cms.post.delete": RiskClass.DESTRUCTIVE,
    "storage.file.delete": RiskClass.DESTRUCTIVE,
    "software.repository.delete": RiskClass.DESTRUCTIVE,
}


def risk_class_for(capability: str) -> str:
    """Clasifica una capability en su clase de riesgo (aprox. determinista)."""
    if capability in RISK_BY_CAPABILITY_PREFIX:
        return RISK_BY_CAPABILITY_PREFIX[capability]
    for prefix, risk in RISK_BY_CAPABILITY_PREFIX.items():
        if prefix.endswith(".") and capability.startswith(prefix):
            return risk
    if capability.endswith((".read", ".get", ".search", ".query", ".list", ".inspect")):
        return RiskClass.READ_ONLY
    if capability.endswith((".delete", ".remove", ".clear", ".cancel")):
        return RiskClass.DESTRUCTIVE
    return RiskClass.LOW_RISK_WRITE


# ------------------------------------------------------------ Canonical ---
class CanonicalContact(BaseModel):
    external_id: Optional[str] = None
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    company_id: Optional[str] = None
    source: Optional[str] = None
    meta: Dict[str, Any] = Field(default_factory=dict)


class CanonicalCalendarEvent(BaseModel):
    external_id: Optional[str] = None
    title: str
    start: Optional[str] = None
    end: Optional[str] = None
    attendees: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)


class CanonicalMessage(BaseModel):
    external_id: Optional[str] = None
    channel: Optional[str] = None
    sender: Optional[str] = None
    recipient: Optional[str] = None
    content: str
    timestamp: Optional[str] = None
    meta: Dict[str, Any] = Field(default_factory=dict)


class canonical_models:
    """Contenedor de los modelos canónicos expuestos a la capa de agentes."""

    CanonicalContact = CanonicalContact
    CanonicalCalendarEvent = CanonicalCalendarEvent
    CanonicalMessage = CanonicalMessage