"""Acciones internas del orquestador (no son capabilities de connector).

Estas acciones las puede proponer el LLM/Proposer sin pasar por el
ConnectorRouter: no hablan con ningun provider externo, son parte del
flujo conversacional del orquestador.

Invariante: los ActionSpec de aqui NO autorizan nada. La Policy del tenant
sigue decidiendo; estas son solo declaraciones para que el LLM sepa que
puede proponerlas.

Se declaran aqui (cognition) y NO en `connectors/core/capability_catalog.py`
para mantener la direccionalidad de dependencias: cognition puede conocer
connectors, pero connectors no debe conocer conceptos de orchestration.
"""
from __future__ import annotations

from typing import Dict

from pydantic import BaseModel, ConfigDict, Field

from ...connectors.core.capability_catalog import ActionSpec
from ...connectors.core.models import RiskClass


class _ReplyToUserParams(BaseModel):
    """Params de la accion interna `reply_to_user`."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    message: str = Field(default="")


INTERNAL_ACTIONS: Dict[str, ActionSpec] = {
    "reply_to_user": ActionSpec(
        kind="reply_to_user",
        providers=(),
        params_schema=_ReplyToUserParams,
        risk=RiskClass.READ_ONLY,
        requires_approval=False,
        description="Responder al usuario sin ejecutar ninguna tool.",
    ),
}


__all__ = ["INTERNAL_ACTIONS", "_ReplyToUserParams"]
