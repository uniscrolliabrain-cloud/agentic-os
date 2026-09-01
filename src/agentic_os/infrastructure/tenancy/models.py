from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field

from ...kernel.types.ids import new_id
from ...kernel.types.time import now_utc
from datetime import datetime


class TenantConfig(BaseModel):
    """Configuración por cliente (tenant). Aísla credenciales, dominio, policy y espacio de datos."""

    model_config = ConfigDict(frozen=True)

    # Identificación
    name: str
    domain: str  # p.ej. "finance", "clinic" — qué vocabulario/taxonomía usa
    logo: Optional[str] = None
    primary_color: str = "#facc15"  # acento UI (estilo DSYS)

    # Aislamiento de datos
    data_dir: str  # ej. "data/tenants/acme"

    # Integraciones habilitadas (nombre de la capability/tool)
    enabled_capabilities: list[str] = Field(default_factory=list)

    # Credenciales de integraciones (OAuth tokens, API keys...) — almacenadas aparte en producción
    credentials: Dict[str, Any] = Field(default_factory=dict)


import re
from pydantic import BaseModel, ConfigDict, Field, field_validator

SLUG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,62}[a-z0-9]?$")


def validate_slug(slug: str) -> str:
    s = slug.strip().lower()
    if not s or not SLUG_PATTERN.match(s) or ".." in s or "/" in s or "\\" in s:
        raise ValueError(
            f"Slug inválido: '{slug}'. Debe contener solo letras minúsculas, números, "
            f"guiones y guiones bajos (1-64 caracteres) y no permitir path traversal."
        )
    return s


class Tenant(BaseModel):
    """Un cliente del sistema agentic multi-tenant."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(default_factory=new_id)
    slug: str  # p.ej. "acme"
    config: TenantConfig
    created_at: datetime = Field(default_factory=now_utc)

    @field_validator("slug")
    @classmethod
    def check_slug(cls, v: str) -> str:
        return validate_slug(v)


class TenantConfigPublic(BaseModel):
    """Vista pública del config de un tenant: NUNCA expone credentials.

    Sustituye a config=s.model_dump() en los endpoints. Si el frontend necesita
    saber si un provider está conectado, usa connected_providers (solo nombres).
    La clase TenantConfig SÍ guarda credentials; esta NO la incluye ni enmascara.
    """

    model_config = ConfigDict(frozen=True)

    name: str
    domain: str
    logo: Optional[str] = None
    primary_color: str = "#facc15"
    data_dir: str
    enabled_capabilities: list[str] = Field(default_factory=list)
    connected_providers: list[str] = Field(default_factory=list)

    @classmethod
    def from_config(cls, config: TenantConfig) -> "TenantConfigPublic":
        return cls(
            name=config.name,
            domain=config.domain,
            logo=config.logo,
            primary_color=config.primary_color,
            data_dir=config.data_dir,
            enabled_capabilities=list(config.enabled_capabilities),
            connected_providers=sorted(config.credentials.keys()),
        )


class TenantContext(BaseModel):
    """El contexto activo de un tenant durante una petición/ejecución."""

    model_config = ConfigDict(frozen=True)

    tenant: Tenant
    roles: list[str] = Field(default_factory=lambda: ["director"])