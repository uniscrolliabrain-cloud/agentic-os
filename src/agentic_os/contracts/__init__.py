"""contracts: modelos Pydantic estrictos compartidos por kernel y ejecución.

FASE 1 — Contratos core (Bloque F).
"""

from .core import InputContract, InputField, OutputContract, OutputField
from .execution import (
    Action,
    ActionParams,
    ActionStatus,
    Command,
    ExecutionResult,
)

__all__ = [
    "Action",
    "ActionParams",
    "ActionStatus",
    "Command",
    "ExecutionResult",
    "InputContract",
    "InputField",
    "OutputContract",
    "OutputField",
]

