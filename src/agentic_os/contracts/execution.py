"""contracts.execution: contratos Pydantic estrictos para Action/Command/Result.

FASE 1.2 — Tipar Command/Action.
Modelos inmutables (frozen=True, extra="forbid", validate_assignment=True).
Sin placeholders: sin Any, sin pass, sin TODO.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator

from ..kernel.types.ids import new_id
from ..kernel.types.time import now_utc

ActionStatus = Literal["pending", "running", "ok", "error", "denied"]


class ActionParams(BaseModel):
    """Parámetros de una Action: mapa tipado clave -> resumen de tipo.

    Los valores son resúmenes de tipo ("<str>", "<int>", ...) para no
    filtrar datos sensibles a la capa de auditoría. Lo produce
    Executor._params_summary y lo consume EventPayload.params.
    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        validate_assignment=True,
    )

    values: Dict[str, str] = Field(
        default_factory=dict,
        description="Mapa nombre-parámetro -> resumen de tipo.",
    )

    @field_validator("values")
    @classmethod
    def _names_nonempty(cls, value: Dict[str, str]) -> Dict[str, str]:
        for name in value:
            if not name or not name.strip():
                raise ValueError(
                    "ActionParams: el nombre de parámetro no puede estar vacío"
                )
        return value


class Action(BaseModel):
    """Acción ejecutable: unidad mínima de efecto del sistema.

    Invariantes:
    - Toda acción pertenece a un tenant (inyectado por el Executor,
      nunca confiado del caller).
    - capability identifica el permiso requerido (PolicyEngine.decide).
    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        validate_assignment=True,
    )

    id: str = Field(default_factory=new_id)
    capability: str = Field(
        min_length=1, description="Capability/permiso requerido."
    )
    actor_id: str = Field(min_length=1, description="Actor que la origina.")
    tenant_id: str = Field(
        default="system", description="Tenant propietario de la acción."
    )
    resource_id: Optional[str] = Field(
        default=None, description="Recurso objetivo opcional."
    )
    params: ActionParams = Field(
        default_factory=ActionParams,
        description="Parámetros tipados (resúmenes de tipo).",
    )
    status: ActionStatus = Field(
        default="pending", description="Estado de la acción."
    )
    created_at: datetime = Field(default_factory=now_utc)

    @field_validator("capability", "actor_id")
    @classmethod
    def _nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("el campo no puede estar en blanco")
        return value


class Command(BaseModel):
    """Comando lógico: misión de alto nivel que agrupa acciones.

    Un Command se descompone en una lista ordenada de Actions.
    correlation_id permite reconstruir Mission -> Pipeline -> Action.
    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        validate_assignment=True,
    )

    id: str = Field(default_factory=new_id)
    name: str = Field(min_length=1, description="Nombre del comando/misión.")
    tenant_id: str = Field(description="Tenant propietario del comando.")
    actor_id: str = Field(min_length=1, description="Actor que lo emite.")
    actions: List[Action] = Field(
        default_factory=list, description="Acciones ordenadas del comando."
    )
    correlation_id: str = Field(
        default_factory=new_id,
        description=(
            "ID de correlación de la ejecución. "
            "Permite reconstruir Mission -> Pipeline -> Action."
        ),
    )
    created_at: datetime = Field(default_factory=now_utc)

    @field_validator("name", "actor_id", "tenant_id")
    @classmethod
    def _nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("el campo no puede estar en blanco")
        return value

    @field_validator("actions")
    @classmethod
    def _same_tenant(
        cls, actions: List[Action], info: ValidationInfo
    ) -> List[Action]:
        tenant = info.data.get("tenant_id")
        for action in actions:
            if tenant is not None and action.tenant_id != tenant:
                raise ValueError(
                    "Command: todas las actions deben pertenecer "
                    f"al tenant del comando ({tenant})"
                )
        return actions


class ExecutionResult(BaseModel):
    """Resultado de ejecutar una Action: éxito/fracaso tipado y auditable."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        validate_assignment=True,
    )

    id: str = Field(default_factory=new_id)
    action_id: str = Field(description="Action que produjo este resultado.")
    success: bool = Field(description="True si la ejecución tuvo éxito.")
    output_keys: List[str] = Field(
        default_factory=list,
        description="Claves de salida (nunca valores: no filtrar datos).",
    )
    error: Optional[str] = Field(
        default=None, description="Error saneado (sin secretos)."
    )
    finished_at: datetime = Field(default_factory=now_utc)
