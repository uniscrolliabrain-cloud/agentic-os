"""StateMachine (spec 05): 7 estados con transiciones validadas."""
from __future__ import annotations

from typing import Dict, FrozenSet

from pydantic import BaseModel, ConfigDict, field_validator


class State(str):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    NEEDS_APPROVAL = "NEEDS_APPROVAL"
    CANCELLED = "CANCELLED"


ALL_STATES: FrozenSet[str] = frozenset({
    State.PENDING, State.RUNNING, State.COMPLETED, State.FAILED,
    State.BLOCKED, State.NEEDS_APPROVAL, State.CANCELLED,
})

assert len(ALL_STATES) == 7, "spec 05 declara 7 estados"


ALLOWED_TRANSITIONS: Dict[str, FrozenSet[str]] = {
    State.PENDING:        frozenset({State.RUNNING, State.CANCELLED}),
    State.RUNNING:        frozenset({State.COMPLETED, State.FAILED, State.BLOCKED, State.NEEDS_APPROVAL}),
    State.COMPLETED:      frozenset(),
    State.FAILED:         frozenset({State.PENDING, State.RUNNING}),
    State.BLOCKED:        frozenset({State.RUNNING}),
    State.NEEDS_APPROVAL: frozenset({State.RUNNING, State.CANCELLED}),
    State.CANCELLED:      frozenset(),
}


class InvalidTransitionError(ValueError):
    """Transicion no permitida por la maquina."""


class StateMachine(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    current: str = State.PENDING

    @field_validator("current")
    @classmethod
    def _current_valido(cls, v: str) -> str:
        if v not in ALL_STATES:
            raise ValueError(f"estado invalido: {v!r}")
        return v

    def can_transition(self, to: str) -> bool:
        if to not in ALL_STATES:
            return False
        return to in ALLOWED_TRANSITIONS[self.current]

    def transition(self, to: str) -> "StateMachine":
        if to not in ALL_STATES:
            raise InvalidTransitionError(f"estado destino invalido: {to!r}")
        if not self.can_transition(to):
            raise InvalidTransitionError(
                f"transicion no permitida: {self.current} -> {to}"
            )
        return StateMachine(current=to)


__all__ = [
    "State", "ALL_STATES", "ALLOWED_TRANSITIONS",
    "InvalidTransitionError", "StateMachine",
]

