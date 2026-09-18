"""Catalogo de los 18 entity types del kernel (spec 03, D03).

Decisiones aplicadas:
- D01: estos 18 tipos son universales (kernel), no de dominio.
- D03: namespace `core.*` (core.person, core.company, ...) para evitar
  colision con DEFAULT_VOCAB. Viven en este fichero, no en `entities.py`
  (que mantiene EntityRef y Entity[T] como maquinaria generica).

Reglas:
- Todos heredan de `CoreEntity` (frozen, extra=forbid, tenant_id obligatorio).
- El campo `kind` es Literal y esta congelado por subclase.
- Los campos marcados como `?` en spec 03 son `Optional[...] = None`.
- Los `list[...]` y `dict[...]` usan `Field(default_factory=...)` cuando el
  spec no los marca como opcionales (listas vacias permitidas, tipo cerrado).

Desviacion documentada:
- Email declara `id?` en spec 03. La base `CoreEntity` ya provee `id: str`
  obligatorio (spec 03: "Toda entidad tiene id"). Se trata como duplicado
  de plantilla y se omite; no se crea un segundo campo id.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import Field, field_validator

from ..types import KernelModel
from ..types.ids import new_id


class CoreEntity(KernelModel):
    """Base para los 18 tipos universales del kernel (namespace core.*)."""

    id: str = Field(default_factory=new_id)
    tenant_id: str

    @field_validator("tenant_id")
    @classmethod
    def _tenant_id_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("tenant_id es obligatorio (invariante multi-tenant)")
        return v


# ---------------------------------------------------------------------------
# 18 entity types (spec 03)
# ---------------------------------------------------------------------------


class Person(CoreEntity):
    kind: Literal["core.person"] = "core.person"
    name: str
    emails: List[str] = Field(default_factory=list)
    phones: List[str] = Field(default_factory=list)
    organization_id: Optional[str] = None
    role: Optional[str] = None


class Organization(CoreEntity):
    kind: Literal["core.organization"] = "core.organization"
    name: str
    website: Optional[str] = None
    domain: Optional[str] = None
    industry: Optional[str] = None


class Company(CoreEntity):
    kind: Literal["core.company"] = "core.company"
    legal_name: str
    name: str
    domain: Optional[str] = None
    size: Optional[str] = None
    industry: Optional[str] = None
    revenue: Optional[float] = None


class Product(CoreEntity):
    kind: Literal["core.product"] = "core.product"
    name: str
    description: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None


class Service(CoreEntity):
    kind: Literal["core.service"] = "core.service"
    name: str
    description: Optional[str] = None
    owner: Optional[str] = None
    category: Optional[str] = None


class Website(CoreEntity):
    kind: Literal["core.website"] = "core.website"
    url: str
    title: Optional[str] = None
    description: Optional[str] = None


class URL(CoreEntity):
    kind: Literal["core.url"] = "core.url"
    url: str
    scheme: str
    host: str
    path: str
    query: Optional[str] = None


class File(CoreEntity):
    kind: Literal["core.file"] = "core.file"
    path: str
    name: str
    format: str
    size_bytes: Optional[int] = None
    hash: Optional[str] = None


class Document(CoreEntity):
    kind: Literal["core.document"] = "core.document"
    title: str
    content: Optional[str] = None
    format: str
    source_url: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Dataset(CoreEntity):
    kind: Literal["core.dataset"] = "core.dataset"
    name: str
    columns: List[str] = Field(default_factory=list)
    rows: int = Field(default=0, ge=0)
    format: str
    source: Optional[str] = None


class Message(CoreEntity):
    kind: Literal["core.message"] = "core.message"
    channel: str
    sender: str
    recipient: str
    content: str
    timestamp: datetime


class Email(CoreEntity):
    kind: Literal["core.email"] = "core.email"
    from_: str
    to: List[str] = Field(default_factory=list)
    cc: List[str] = Field(default_factory=list)
    subject: str
    body: str


class SocialPost(CoreEntity):
    kind: Literal["core.social_post"] = "core.social_post"
    platform: str
    content: str
    media: List[str] = Field(default_factory=list)
    scheduled_at: Optional[datetime] = None
    status: str


class Image(CoreEntity):
    kind: Literal["core.image"] = "core.image"
    url: Optional[str] = None
    path: Optional[str] = None
    prompt: Optional[str] = None
    format: str
    size_bytes: int = Field(default=0, ge=0)


class Video(CoreEntity):
    kind: Literal["core.video"] = "core.video"
    url: Optional[str] = None
    path: Optional[str] = None
    script: Optional[str] = None
    duration_sec: Optional[int] = None
    format: str


class Audio(CoreEntity):
    kind: Literal["core.audio"] = "core.audio"
    url: Optional[str] = None
    path: Optional[str] = None
    transcript: Optional[str] = None
    format: str


class Event(CoreEntity):
    kind: Literal["core.event"] = "core.event"
    type: str
    at: datetime
    actor_id: str
    entity_id: str
    payload: Dict[str, Any] = Field(default_factory=dict)


class Task(CoreEntity):
    kind: Literal["core.task"] = "core.task"
    title: str
    description: Optional[str] = None
    assignee: Optional[str] = None
    status: str
    due: Optional[datetime] = None
    dependencies: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

CORE_ENTITY_TYPES: tuple[type[CoreEntity], ...] = (
    Person, Organization, Company, Product, Service, Website, URL, File,
    Document, Dataset, Message, Email, SocialPost, Image, Video, Audio,
    Event, Task,
)

CORE_ENTITY_KIND_TO_CLASS: Dict[str, type[CoreEntity]] = {
    cls.model_fields["kind"].default: cls for cls in CORE_ENTITY_TYPES
}

assert len(CORE_ENTITY_TYPES) == 18, "spec 03 declara exactamente 18 tipos"
assert len(CORE_ENTITY_KIND_TO_CLASS) == 18, "kinds unicos"


__all__ = [
    "CoreEntity",
    "CORE_ENTITY_TYPES",
    "CORE_ENTITY_KIND_TO_CLASS",
    "Person", "Organization", "Company", "Product", "Service",
    "Website", "URL", "File", "Document", "Dataset", "Message",
    "Email", "SocialPost", "Image", "Video", "Audio", "Event", "Task",
]

