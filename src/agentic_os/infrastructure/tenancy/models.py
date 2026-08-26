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


class Tenant(BaseModel):
    """Un cliente del sistema agentic multi-tenant."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(default_factory=new_id)
    slug: str  # p.ej. "acme"
    config: TenantConfig
    created_at: datetime = Field(default_factory=now_utc)


class TenantContext(BaseModel):
    """El contexto activo de un tenant durante una petición/ejecución."""

    model_config = ConfigDict(frozen=True)

    tenant: Tenant
    roles: list[str] = Field(default_factory=lambda: ["director"])