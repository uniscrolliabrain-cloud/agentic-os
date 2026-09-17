"""Arquetipos Pydantic de parametros para capabilities de conectores.

Este modulo define los SHAPES canonicos de params. Cada capability del
catalogo (`PROVIDER_SPECS`) declara UN schema de aqui (o uno especifico
definido en el propio provider). El loader `capability_catalog.py` los
usa para validar los payloads que el LLM propone.

Invariante: los schemas son `frozen=True, extra="forbid"`. Lo que no
valida, no se propone. Lo que no se propone, no se ejecuta.

NO confundir con la taxonomia de riesgo (`RiskClass` en `core/models.py`).
El `risk` de una capability es METADATA para el LLM. El endurecimiento
duro (delete/publish -> require_approval) vive en `PolicyEvaluator` y NO
se puede saltar declarando un risk mas bajo aqui.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class _StrictParams(BaseModel):
    """Base para params de capability: inmutable y sin campos extra."""

    model_config = ConfigDict(frozen=True, extra="forbid")


# ---------------------------------------------------------------------------
# Arquetipos por accion
# ---------------------------------------------------------------------------

class ReadParams(_StrictParams):
    """Leer un recurso por id o referencia."""

    id: str = Field(default="", description="Identificador del recurso")
    query: str = Field(default="", description="Consulta opcional de filtrado")


class ListParams(_StrictParams):
    """Listar recursos con filtros opcionales."""

    query: str = Field(default="", description="Filtro opcional")
    folder: str = Field(default="", description="Carpeta o contenedor")
    max_results: int = Field(default=20, ge=1, le=200)


class SearchParams(_StrictParams):
    """Buscar dentro de un universo conocido."""

    query: str = Field(min_length=1, description="Texto a buscar")
    max_results: int = Field(default=10, ge=1, le=200)


class SendParams(_StrictParams):
    """Enviar un mensaje (email, slack, whatsapp, etc.)."""

    to: str = Field(min_length=1, description="Destinatario")
    subject: str = Field(default="")
    body: str = Field(min_length=1, description="Contenido del mensaje")
    cc: List[str] = Field(default_factory=list)

    @field_validator("to")
    @classmethod
    def _to_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("to no puede estar en blanco")
        return v


class CreateParams(_StrictParams):
    """Crear un recurso con un payload generico."""

    payload: Dict[str, Any] = Field(default_factory=dict)


class UpdateParams(_StrictParams):
    """Actualizar campos de un recurso existente."""

    id: str = Field(min_length=1)
    changes: Dict[str, Any] = Field(default_factory=dict)


class DeleteParams(_StrictParams):
    """Borrar un recurso por id. Requiere aprobacion humana (invariante)."""

    id: str = Field(min_length=1)


class PublishParams(_StrictParams):
    """Publicar contenido. Requiere aprobacion humana (invariante)."""

    channel: str = Field(min_length=1, description="Canal (meta, linkedin, etc.)")
    content: str = Field(min_length=1)
    asset_url: str = Field(default="")


# ---------------------------------------------------------------------------
# Especificos por familia (los que no encajan en un arquetipo generico)
# ---------------------------------------------------------------------------

class FileReadParams(_StrictParams):
    """Leer el contenido de un fichero."""

    path: str = Field(min_length=1)
    file_id: str = Field(default="")


class FileWriteParams(_StrictParams):
    """Escribir contenido en un fichero."""

    path: str = Field(min_length=1)
    content: str = Field(min_length=1)
    mime_type: str = Field(default="text/plain")


class FileDeleteParams(_StrictParams):
    """Borrar un fichero. Requiere aprobacion humana (invariante)."""

    path: str = Field(default="")
    file_id: str = Field(default="")

    @field_validator("path", "file_id")
    @classmethod
    def _al_menos_uno(cls, v: str, info) -> str:
        return v


class CalendarEventParams(_StrictParams):
    """Crear o modificar un evento de calendario."""

    title: str = Field(min_length=1)
    start: str = Field(min_length=1, description="ISO 8601 con timezone")
    end: str = Field(default="", description="ISO 8601; vacio -> se usa start")
    attendees: List[str] = Field(default_factory=list)


class CalendarListParams(_StrictParams):
    """Listar eventos del calendario."""

    max_results: int = Field(default=10, ge=1, le=200)
    time_min: str = Field(default="")
    time_max: str = Field(default="")


class WebSearchParams(_StrictParams):
    """Buscar en la web."""

    query: str = Field(min_length=1)
    max_results: int = Field(default=10, ge=1, le=50)


class WebScrapeParams(_StrictParams):
    """Extraer el contenido de una URL."""

    url: str = Field(min_length=5)
    selector: str = Field(default="")


class ContactCreateParams(_StrictParams):
    """Crear un contacto en un CRM."""

    name: str = Field(min_length=1)
    email: str = Field(default="")
    phone: str = Field(default="")
    company: str = Field(default="")


class CompanyCreateParams(_StrictParams):
    """Crear una empresa en un CRM."""

    name: str = Field(min_length=1)
    domain: str = Field(default="")
    industry: str = Field(default="")


class PaymentLinkParams(_StrictParams):
    """Crear un link de pago. Requiere aprobacion humana (invariante)."""

    amount_cents: int = Field(ge=1)
    currency: str = Field(default="eur", min_length=3, max_length=3)
    description: str = Field(default="")


class GenericParams(_StrictParams):
    """Fallback para capabilities sin schema especifico.

    NO autoriza nada: es solo un contenedor. La capability sigue pasando
    por Policy. Si un provider declara esta clase, significa que su
    payload no tiene shape fijo. Casos asi son raros; preferir siempre
    un arquetipo concreto.
    """

    payload: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Mapa de arquetipos por convencion (sufijo del kind -> clase)
# ---------------------------------------------------------------------------

# El loader `capability_catalog.py` usara este mapa para resolver la clase
# de params cuando el provider no declare una explicitamente.
# Fallback: 'GenericParams' (contenedor libre, sin efecto en policy).
ARCHETYPE_BY_SUFFIX: Dict[str, type[_StrictParams]] = {
    ".read": ReadParams,
    ".list": ListParams,
    ".search": SearchParams,
    ".send": SendParams,
    ".create": CreateParams,
    ".update": UpdateParams,
    ".delete": DeleteParams,
    ".publish": PublishParams,
}


def archetype_for_kind(kind: str) -> type[_StrictParams]:
    """Devuelve la clase de params por convencion de sufijo.

    Si el kind no matchea ningun sufijo del mapa, devuelve GenericParams.
    El provider puede sobrescribir el arquetipo declarando el suyo en
    `PROVIDER_SPECS[provider]['capabilities'][kind]['schema']`.
    """
    if not kind:
        return GenericParams
    for suffix, cls in ARCHETYPE_BY_SUFFIX.items():
        if kind.endswith(suffix):
            return cls
    return GenericParams


__all__ = [
    "ReadParams",
    "ListParams",
    "SearchParams",
    "SendParams",
    "CreateParams",
    "UpdateParams",
    "DeleteParams",
    "PublishParams",
    "FileReadParams",
    "FileWriteParams",
    "FileDeleteParams",
    "CalendarEventParams",
    "CalendarListParams",
    "WebSearchParams",
    "WebScrapeParams",
    "ContactCreateParams",
    "CompanyCreateParams",
    "PaymentLinkParams",
    "GenericParams",
    "ARCHETYPE_BY_SUFFIX",
    "archetype_for_kind",
]