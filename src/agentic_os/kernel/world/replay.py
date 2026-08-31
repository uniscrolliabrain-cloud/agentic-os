from __future__ import annotations
from typing import Any

from .state import WorldState
from .applier import apply


def replay(log: Any) -> WorldState:
    """Reconstruye el WorldState desde cualquier EventLogRepository.

    FASE 3.1 (bugfix de tipo en kernel/, no feature): antes leía
    `log.events` directamente — atributo que solo existe en el EventLog
    in-memory de tests — y con JsonlEventLog/PostgresEventLog habría
    lanzado AttributeError en runtime. Ahora usa el método de interfaz
    común `all_events()`, implementado por los tres repositorios.
    """
    state = WorldState()
    for e in log.all_events():
        state = apply(state, e)
    return state
