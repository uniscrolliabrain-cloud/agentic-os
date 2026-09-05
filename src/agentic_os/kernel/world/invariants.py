from __future__ import annotations
from typing import List

from .state import WorldState

# Lista de invariantes para documentación
INVARIANTS = [
    "Event immutable",
    "Log append-only",
    "State derivable",
    "apply pure",
    "version +1 per event",
]


def validate_state(state: WorldState) -> bool:
    """Valida las invariantes del WorldState.

    Returns:
        True si el estado es válido, False si viola alguna invariante.
    """
    # Invariante: version no puede ser negativo
    if state.version < 0:
        return False
    # Invariante: entities debe ser un dict
    if not isinstance(state.entities, dict):
        return False
    # Invariante: relations debe ser un dict
    if not isinstance(state.relations, dict):
        return False
    return True


def check_invariants(state: WorldState) -> List[str]:
    """Devuelve lista de violaciones de invariantes (lista vacía = OK)."""
    violations: List[str] = []
    if state.version < 0:
        violations.append("version negativa")
    if not isinstance(state.entities, dict):
        violations.append("entities no es dict")
    if not isinstance(state.relations, dict):
        violations.append("relations no es dict")
    return violations
