"""Entidades de dominio tipadas — kernel SOLO provee la MAQUINARIA.

El kernel define:
- ``BaseDomainModel`` — base estricta (frozen, forbid, tenant_id obligatorio).
- ``register_entity_types()`` — registro EXPLÍCITO de clases de dominio.
- ``entity_from_payload()`` — construcción fail-closed desde kind + payload.
- ``validate_registry_integrity()`` — coherencia clave ↔ Literal kind.
- ``UnknownEntityTypeError``.

El kernel NO define entidades concretas (Lead, AgencyClient, BlogPost…).
Cada dominio (``domains/<slug>/``) aporta las suyas y las registra
explícitamente en su bootstrap (``XxxDomain.register_entities()``).

Invariante (docs/INVARIANTS.md I5): ``ENTITY_TYPE_REGISTRY`` ARRANCA VACÍO
en import. Se puebla solo por llamada explícita a ``register_entity_types()``.
Ningún módulo muta el registro como side-effect de import.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ..types.ids import new_id
from ..types.time import now_utc


class BaseDomainModel(BaseModel):
    """Base estricta para entidades de dominio."""

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
        if isinstance(data, dict):
            kind = data.get("kind")
            if "entity_type" not in data and kind is not None:
                data["entity_type"] = kind
            elif "entity_type" not in data:
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
            raise ValueError("entity_type es obligatorio (discriminador)")
        return v

    @field_validator("version")
    @classmethod
    def _version_no_negativa(cls, v: int) -> int:
        if v < 0:
            raise ValueError("version no puede ser negativa")
        return v

    @model_validator(mode="after")
    def _sync_entity_type_from_kind(self) -> "BaseDomainModel":
        kind_val = getattr(self, "kind", None)
        if kind_val is not None and not self.entity_type:
            object.__setattr__(self, "entity_type", kind_val)
        return self


DomainEntity = BaseDomainModel


from .entities import EntityRef  # noqa: E402


ENTITY_TYPE_REGISTRY: dict[str, type[BaseDomainModel]] = {}


class UnknownEntityTypeError(KeyError):
    """Se pidió un kind no registrado en ENTITY_TYPE_REGISTRY (fail-closed)."""


def register_entity_types(
    *classes: type[BaseDomainModel],
    registry: dict[str, type[BaseDomainModel]] | None = None,
) -> None:
    """Registra clases de entidad de dominio EXPLÍCITAMENTE (bootstrap)."""
    target = ENTITY_TYPE_REGISTRY if registry is None else registry
    for cls in classes:
        kind_field = cls.model_fields.get("kind")
        kind = getattr(kind_field, "default", None) if kind_field else None
        if not kind:
            raise ValueError(
                f"{cls.__name__} no declara kind Literal con default; "
                "no puede registrarse en ENTITY_TYPE_REGISTRY"
            )
        existing = target.get(kind)
        if existing is not None and existing is not cls:
            raise ValueError(
                f"kind '{kind}' ya registrado por {existing.__name__}; "
                f"no se sobrescribe con {cls.__name__}"
            )
        target[kind] = cls


def entity_from_payload(kind: str, data: dict[str, Any]) -> BaseDomainModel:
    """Construye una entidad tipada desde kind + payload (fail-closed)."""
    cls = ENTITY_TYPE_REGISTRY.get(kind)
    if cls is None:
        raise UnknownEntityTypeError(
            f"entity_type '{kind}' no registrado en ENTITY_TYPE_REGISTRY"
        )
    return cls(**data)


def validate_registry_integrity() -> None:
    """Coherencia clave ↔ Literal kind de cada clase."""
    for key, cls in ENTITY_TYPE_REGISTRY.items():
        kind_field = cls.model_fields.get("kind")
        default_kind = getattr(kind_field, "default", None) if kind_field else None
        if kind_field is None or default_kind != key:
            raise ValueError(
                f"ENTITY_TYPE_REGISTRY corrupto: clave '{key}' no coincide "
                f"con el kind de {cls.__name__}"
            )


__all__ = [
    "BaseDomainModel",
    "DomainEntity",
    "EntityRef",
    "ENTITY_TYPE_REGISTRY",
    "UnknownEntityTypeError",
    "register_entity_types",
    "entity_from_payload",
    "validate_registry_integrity",
]
