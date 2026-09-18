"""execution.action - Version LAXA de Action (legacy).

AUD-15: coexiste con contracts/execution.py::Action (version estricta,
con tenant_id obligatorio, ActionParams tipado, extra=forbid).

Esta version laxa la usa internamente el Executor para callers legacy
que pasan un Action. La version estricta de contracts/ es el contrato
canonico del kernel.

Migracion pendiente: cuando Executor unifique su firma para usar
ActionParams en vez de dict, esta clase se eliminara.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from ..kernel.types.ids import new_id
from ..kernel.types.time import now_utc


class Action(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str = Field(default_factory=new_id)
    capability: str
    actor_id: str
    resource_id: Optional[str] = None
    params: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=now_utc)