"""execution.result - Version LAXA de ExecutionResult (legacy).

AUD-15: coexiste con contracts/execution.py::ExecutionResult (version
estricta con output_keys en vez de output: nunca filtra valores).

El Executor.execute() real retorna dicts planos
({success: ..., output: ...}), no instancias de ninguna de las dos.
La migracion esta pendiente.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from ..kernel.types.ids import new_id


class ExecutionResult(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str = Field(default_factory=new_id)
    action_id: str
    success: bool
    output: dict = Field(default_factory=dict)
    error: Optional[str] = None