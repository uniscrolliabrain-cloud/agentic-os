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
    """Comprueba si un patron coincide: '*' todo, 'a.b.*' prefijo, else exacto.

    AUD-12: antes solo soportaba '*' global o match exacto. Ahora soporta
    namespaces por sufijo (p.ej. 'crm.contact.*' coincide con
    'crm.contact.create' y 'crm.contact.read').
    """
    if pattern is None:
        return True
    if pattern == "*":
        return True
    if pattern.endswith(".*"):
        return bool(value) and value.startswith(pattern[:-1])
    return pattern == value


class PolicyEvaluator:
    """EvalÃƒÂºa una acciÃƒÂ³n contra las reglas de la policy de forma determinista.

    Si ninguna regla coincide, la acciÃƒÂ³n se DENIEGA por defecto (default-deny):
    el sistema nunca permite algo que no estÃƒÂ© explÃƒÂ­citamente estipulado.

    INVARIANTE DEL KERNEL (no negociable): las acciones destructivas o de
    publicaciÃƒÂ³n (delete/publish) SIEMPRE requieren aprobaciÃƒÂ³n humana. Una
    regla explÃƒÂ­cita puede aÃƒÂ±adir mÃƒÂ¡s restricciones, nunca quitar esta.
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
        # AUD-12: precedencia por especificidad + endurecimiento por riesgo.
        # 1. Especificidad: una regla exacta gana sobre una de namespace, y
        #    esta sobre una de wildcard "*".
        # 2. Dentro del mismo nivel: deny > require_approval > allow.
        # 3. Endurecimiento del kernel: delete/publish/FINANCIAL exige approval
        #    incluso si una regla allow lo permitiria.
        matching = []
        for rule in self.policy.rules:
            if not _matches(rule.capability, capability):
                continue
            if not _matches(rule.resource_kind, resource_kind):
                continue
            if rule.requires_roles and not any(r in roles for r in rule.requires_roles):
                continue
            matching.append(rule)

        if not matching:
            return Decision(effect="deny", reason="no matching rule")

        def _specificity(pattern):
            if pattern is None or pattern == "*":
                return 1
            if pattern.endswith(".*"):
                return 2
            return 3

        top_spec = max(_specificity(r.capability) for r in matching)
        top = [r for r in matching if _specificity(r.capability) == top_spec]

        # Precedencia dentro del nivel mas especifico que casa.
        for rule in top:
            if rule.effect == "deny":
                return Decision(effect="deny", rule_id=rule.id, reason=rule.description)

        for rule in top:
            if rule.effect == "require_approval":
                return Decision(effect="require_approval", rule_id=rule.id, reason=rule.description)

        for rule in top:
            if rule.effect == "allow":
                if self._requires_human_approval(capability):
                    return Decision(
                        effect="require_approval",
                        rule_id=rule.id,
                        reason="invariante del kernel: la capability exige aprobacion humana",
                    )
                return Decision(effect="allow", rule_id=rule.id, reason=rule.description)

        return Decision(effect="deny", reason="no matching rule")