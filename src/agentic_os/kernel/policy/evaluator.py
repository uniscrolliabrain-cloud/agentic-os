from __future__ import annotations
from pydantic import BaseModel, ConfigDict
from typing import Optional, Literal
from .models import Effect


class Decision(BaseModel):
    model_config = ConfigDict(frozen=True)
    effect: Effect
    rule_id: Optional[str] = None
    reason: str = ""


def _matches(pattern: Optional[str], value: Optional[str]) -> bool:
    """Comprueba si un patrón coincide: '*' coincide con cualquier valor."""
    if pattern is None:
        return True
    if pattern == "*":
        return True
    return pattern == value


class PolicyEvaluator:
    """Evalúa una acción contra las reglas de la policy de forma determinista.

    Si ninguna regla coincide, la acción se DENIEGA por defecto (default-deny):
    el sistema nunca permite algo que no esté explícitamente estipulado.
    """

    def __init__(self, policy):
        self.policy = policy

    def evaluate(self, capability: str, resource_kind: Optional[str], roles: list[str]) -> Decision:
        for rule in self.policy.rules:
            if not _matches(rule.capability, capability):
                continue
            if not _matches(rule.resource_kind, resource_kind):
                continue
            if rule.requires_roles and not any(r in roles for r in rule.requires_roles):
                continue
            return Decision(effect=rule.effect, rule_id=rule.id, reason=rule.description)
        return Decision(effect="deny", reason="no matching rule")