from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from .ids import new_id
from .time import now_utc


class KernelModel(BaseModel):
    """Base inmutable para todo el kernel.

    - frozen=True: inmutabilidad garantizada
    - extra=forbid: rechaza campos inesperados
    - validate_assignment=True: valida siempre
    - use_enum_values=True: almacena valores, no wrappers
    """
    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        validate_assignment=True,
        use_enum_values=True,
    )


__all__ = ["KernelModel", "new_id", "now_utc"]
