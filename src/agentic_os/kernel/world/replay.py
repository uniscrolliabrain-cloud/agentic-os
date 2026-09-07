from __future__ import annotations
from typing import Any

from .state import WorldState
from .applier import apply


class CorruptEventError(RuntimeError):
    """Un evento del log es invalido y no puede aplicarse.

    A8: el replay NUNCA continua ni devuelve un estado parcial; la excepcion
    indica el indice del evento corrupto dentro del log.
    """

    def __init__(self, index: int, event_id: str, kind: str, cause: Exception):
        self.index = index
        self.event_id = event_id
        self.kind = kind
        self.cause = cause
        super().__init__(
            f"Evento corrupto en indice {index} (id={event_id}, kind={kind}): "
            f"{cause}"
        )


def replay(log: Any) -> WorldState:
    """Reconstruye el WorldState desde cualquier EventLogRepository.

    A8 (fail-closed): si un evento no puede aplicarse (payload invalido,
    entidad no registrada, update sobre entidad inexistente), se lanza
    CorruptEventError indicando el indice del evento — nunca se devuelve
    un WorldState parcial ni se omite el fallo silenciosamente.
    """
    state = WorldState()
    for index, e in enumerate(log.all_events()):
        try:
            state = apply(state, e)
        except Exception as exc:  # noqa: BLE001 - se relanza tipado abajo
            raise CorruptEventError(
                index=index, event_id=e.id, kind=e.kind, cause=exc
            ) from exc
    return state