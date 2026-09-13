from __future__ import annotations
from typing import Generic, TypeVar

from pydantic import Field, field_validator

from ..types import KernelModel

T = TypeVar("T")


class EntityRef(KernelModel):
    """Ref de identidad del kernel.

    Vive aqui (y NO en ``domain_models``) para que ``kernel.ontology.entities``
    no dependa de ``domain_models``: ese era el ciclo que rompia la carga de
    dominios. Se re-exporta desde ``domain_models`` por compatibilidad.
    """

    tenant_id: str
    entity_id: str
    entity_type: str

    @field_validator("tenant_id")
    @classmethod
    def _tenant_id_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("tenant_id es obligatorio (invariante multi-tenant)")
        return v

    @field_validator("entity_id")
    @classmethod
    def _entity_id_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("entity_id es obligatorio")
        return v

    @field_validator("entity_type")
    @classmethod
    def _entity_type_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("entity_type es obligatorio (discriminador)")
        return v

    @classmethod
    def from_entity(cls, entity: object) -> "EntityRef":
        """Construye un EntityRef desde una entidad de dominio tipada."""
        tenant_id = str(getattr(entity, "tenant_id", ""))
        entity_id = str(getattr(entity, "id", ""))
        entity_type = str(
            getattr(entity, "kind", None) or getattr(entity, "entity_type", "")
        )
        return cls(
            tenant_id=tenant_id, entity_id=entity_id, entity_type=entity_type
        )


class Entity(KernelModel, Generic[T]):
    """Entidad tipada del kernel.

    - ref: identidad, tenant y tipo de entidad.
    - data: la entidad de dominio tipada (T).
    """

    ref: EntityRef
    data: T

    @property
    def id(self) -> str:
        return self.ref.entity_id

    @property
    def kind(self) -> str:
        """Discriminador de tipo (delegado en ref.entity_type).

        `OntologyValidator.validate_entity` y los tests de contratos usan
        `e.kind`; mantenerlo como property evita duplicar el campo.
        """
        return self.ref.entity_type

