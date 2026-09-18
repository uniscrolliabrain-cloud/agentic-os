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

    # AUD-13: segmentos de capability que activan el invariante de aprobacion
    # humana. Antes solo {delete, publish}; ahora tambien las clases
    # FINANCIAL y DESTRUCTIVE declaradas en README.md.
    INVARIANT_APPROVAL_SEGMENTS = frozenset({
        "delete", "remove", "clear", "cancel",
        "publish", "send",
        "refund",
    })
    # Prefijos que fuerzan aprobacion (FINANCIAL / DESTRUCTIVE por familia).
    INVARIANT_APPROVAL_PREFIXES = (
        "finance.", "payment.", "stripe.", "billing.",
    )

    def __init__(self, policy):
        self.policy = policy

    @staticmethod
    def _requires_human_approval(capability: str) -> bool:
        cap = capability or ""
        segments = {seg.lower() for seg in cap.split(".") if seg}
        if segments & PolicyEvaluator.INVARIANT_APPROVAL_SEGMENTS:
            return True
        return cap.startswith(PolicyEvaluator.INVARIANT_APPROVAL_PREFIXES)

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