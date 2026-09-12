from __future__ import annotations
from datetime import datetime
from typing import Generic, TypeVar

from pydantic import ConfigDict

from ..types import KernelModel
from ..ontology.domain_models import BaseDomainModel, EntityRef

T = TypeVar("T", bound=BaseDomainModel)


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
        return self.data.entity_type

    @property
    def entity_type(self) -> str:
        return self.ref.entity_type

    @property
    def tenant_id(self) -> str:
        return self.ref.tenant_id

    @property
    def created_at(self) -> datetime:
        return self.data.created_at

