from __future__ import annotations

from typing import Optional

from .approval import ApprovalRequest
from .evaluator import Decision, PolicyEvaluator
from .models import Policy, PolicyRule


def default_policy() -> Policy:
    """Política por defecto: permite TODAS las capabilities a cualquier rol.

    En producción cada tenant tendría su propia política restrictiva.
    Esta default-allow permite que el sistema arranque y sea probable,
    pero el policy engine está listo para aplicar reglas estrictas.
    """
    return Policy(
        id="default",
        name="default-allow",
        rules=[
            PolicyRule(
                id="allow-all",
                capability="*",
                effect="allow",
                requires_roles=[],
                description="Default allow: todas las capabilities permitidas en desarrollo",
            )
        ],
    )


class PolicyEngine:
    """Motor de políticas determinista.

    Decide SI una acción está permitida ANTES de que se ejecute.
    El LLM propone, la policy decide, y solo entonces el executor ejecuta.
    """

    def __init__(self, policy: Optional[Policy] = None):
        self.policy = policy or default_policy()
        self.evaluator = PolicyEvaluator(self.policy)

    def can(
        self,
        capability: str,
        resource_kind: Optional[str] = None,
        roles: Optional[list[str]] = None,
    ) -> Decision:
        return self.evaluator.evaluate(capability, resource_kind, roles or [])

    def is_allowed(self, tenant_id: str, action: str) -> bool:
        """Comprueba si una acción está permitida para un tenant.

        Por ahora usa la política global; en producción miraría la policy
        específica del tenant (aislamiento multi-tenant).
        """
        decision = self.evaluator.evaluate(action, None, [])
        return decision.effect == "allow"

    def requires_approval(self, decision: Decision) -> bool:
        return decision.effect == "require_approval"

    def request_approval(
        self,
        actor_id: str,
        capability: str,
        resource_id: Optional[str] = None,
    ) -> ApprovalRequest:
        return ApprovalRequest(
            actor_id=actor_id,
            capability=capability,
            resource_id=resource_id,
        )