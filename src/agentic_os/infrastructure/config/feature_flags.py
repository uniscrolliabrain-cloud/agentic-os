"""Feature flags de infraestructura (BUILD_PLAN 0b).

Regla: el codigo NUNCA sabe si algo esta on u off. Los contratos son
los mismos. Solo cambia la implementacion detras del flag.

Default: TODO OFF (excepto WEB_SEARCH, que es gratis).
Activacion por env var: ENABLE_<NOMBRE>=true.
"""
from __future__ import annotations

import os
from typing import Dict

from pydantic import BaseModel, ConfigDict, Field


_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in _TRUE_VALUES


class FeatureFlags(BaseModel):
    """Flags de infraestructura y conectores.

    - Infra pesada: default OFF. Se activa cuando duele.
    - Conectores: default OFF. Se activan por tenant o entorno.
    - Web Search: default ON (gratis).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    # Infra pesada (default OFF)
    temporal: bool = Field(default=False)
    supabase: bool = Field(default=False)
    jwt: bool = Field(default=False)
    obs: bool = Field(default=False)
    redis: bool = Field(default=False)
    docker: bool = Field(default=False)

    # Conectores (default OFF)
    gmail: bool = Field(default=False)
    drive: bool = Field(default=False)
    calendar: bool = Field(default=False)
    discord: bool = Field(default=False)

    # Web Search: default ON (gratis)
    web_search: bool = Field(default=True)

    def is_enabled(self, name: str) -> bool:
        """True si el flag esta on. Fail-closed si no existe."""
        field = name.strip().lower().replace("-", "_")
        if field not in type(self).model_fields:
            return False
        return bool(getattr(self, field))

    def as_dict(self) -> Dict[str, bool]:
        return {k: bool(getattr(self, k)) for k in type(self).model_fields}


def load_feature_flags() -> FeatureFlags:
    """Carga los flags desde env vars. Idempotente."""
    return FeatureFlags(
        temporal=_env_bool("ENABLE_TEMPORAL", False),
        supabase=_env_bool("ENABLE_SUPABASE", False),
        jwt=_env_bool("ENABLE_JWT", False),
        obs=_env_bool("ENABLE_OBS", False),
        redis=_env_bool("ENABLE_REDIS", False),
        docker=_env_bool("ENABLE_DOCKER", False),
        gmail=_env_bool("ENABLE_GMAIL", False),
        drive=_env_bool("ENABLE_DRIVE", False),
        calendar=_env_bool("ENABLE_CALENDAR", False),
        discord=_env_bool("ENABLE_DISCORD", False),
        web_search=_env_bool("ENABLE_WEB_SEARCH", True),
    )


flags = load_feature_flags()


__all__ = ["FeatureFlags", "load_feature_flags", "flags"]

