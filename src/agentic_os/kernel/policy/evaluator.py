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

    INVARIANTE DEL KERNEL (no negociable): las acciones destructivas o de
    publicación (delete/publish) SIEMPRE requieren aprobación humana. Una
    regla explícita puede añadir más restricciones, nunca quitar esta.
    """

    # Segmentos de capability que activan el invariante de aprobación humana.
    INVARIANT_APPROVAL_SEGMENTS = frozenset({"delete", "publish"})

    def __init__(self, policy):
        self.policy = policy

    @staticmethod
    def _requires_human_approval(capability: str) -> bool:
        segments = {seg.lower() for seg in capability.split(".")}
        return bool(segments & PolicyEvaluator.INVARIANT_APPROVAL_SEGMENTS)

    def evaluate(self, capability: str, resource_kind: Optional[str], roles: list[str]) -> Decision:
        for rule in self.policy.rules:
            if not _matches(rule.capability, capability):
                continue
            if not _matches(rule.resource_kind, resource_kind):
                continue
            if rule.requires_roles and not any(r in roles for r in rule.requires_roles):
                continue
            effect = rule.effect
            # Invariante del kernel: una regla puede endurecer, nunca suavizar.
            if effect == "allow" and self._requires_human_approval(capability):
                return Decision(
                    effect="require_approval",
                    rule_id=rule.id,
                    reason=f"invariante del kernel: '{capability}' es destructiva/publicable y exige aprobación humana",
                )
            return Decision(effect=effect, rule_id=rule.id, reason=rule.description)
        return Decision(effect="deny", reason="no matching rule")