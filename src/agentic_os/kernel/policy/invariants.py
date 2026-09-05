from __future__ import annotations
from typing import List

from .models import Policy

# Lista de invariantes para documentación
INVARIANTS = [
    "Policy immutable",
    "Deny by default",
    "Approval != granted",
    "Engine pure",
]


def validate_policy(policy: Policy) -> bool:
    """Valida las invariantes de la Policy.

    Returns:
    True si la policy es válida, False si viola alguna invariante.
    """
    # Invariante: deny por defecto (rules vacío = deny todo)
    # Invariante: no puede haber rules con capability vacía
    for rule in policy.rules:
        if not rule.capability:
            return False
    return True


def check_invariants(policy: Policy) -> List[str]:
    """Devuelve lista de violaciones de invariantes (lista vacía = OK)."""
    violations: List[str] = []
    for rule in policy.rules:
        if not rule.capability:
            violations.append(f"rule {rule.id} sin capability")
    return violations
