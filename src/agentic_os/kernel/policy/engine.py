from __future__ import annotations

from typing import Optional
import os
import json
from pathlib import Path

from.approval import ApprovalRequest
from.evaluator import Decision, PolicyEvaluator
from.models import Policy, PolicyRule
from...infrastructure.config.settings import settings

def default_policy(tenant_id: str = "default") -> Policy:
    """
    Política por defecto POR TENANT.
    - En dev: allow-all para poder arrancar.
    - En prod: deny-all. Nunca capability="*" global.
    """
    is_dev = settings.env == "dev"

    if is_dev:
        return Policy(
            id=f"default-{tenant_id}",
            name=f"default-allow-{tenant_id}",
            rules=[
                PolicyRule(
                    id=f"allow-all-{tenant_id}",
                    capability="*",
                    effect="allow",
                    requires_roles=[],
                    description=f"Default allow SOLO en dev para tenant {tenant_id}",
                )
            ],
        )
    else:
        # Prod: sin reglas = deny by default
        return Policy(
            id=f"default-{tenant_id}",
            name=f"default-deny-{tenant_id}",
            rules=[],
        )

class PolicyEngine:
    """Motor de políticas determinista con aislamiento multi-tenant."""

    def __init__(self, policy: Optional[Policy] = None, tenant_id: str = "default"):
        self.tenant_id = tenant_id
        self.policy = policy or default_policy(tenant_id)
        self.evaluator = PolicyEvaluator(self.policy)

    def _load_tenant_policy(self, tenant_id: str) -> Optional[Policy]:
        """Intenta cargar data/policies/{tenant_id}.json si existe."""
        policy_path = Path(f"data/policies/{tenant_id}.json")
        if policy_path.exists():
            try:
                data = json.loads(policy_path.read_text(encoding="utf-8"))
                return Policy(**data)
            except Exception:
                return None
        return None

    def can(
        self,
        capability: str,
        resource_kind: Optional[str] = None,
        roles: Optional[list[str]] = None,
    ) -> Decision:
        # En prod, si estamos con default allow-all, denegar
        if settings.env!= "dev":
            if any(r.capability == "*" and r.effect == "allow" for r in self.policy.rules):
                # Estamos en prod con política de dev -> bloquear
                from.models import Decision as DecisionModel # evitar circular si existe
                # Creamos decision manual deny
                return Decision(effect="deny", reason="default-allow no permitido en prod")

        return self.evaluator.evaluate(capability, resource_kind, roles or [])

    def is_allowed(self, tenant_id: str, action: str) -> bool:
        """
        AHORA SÍ mira policy del tenant. No global.
        """
        # 1. Intentar cargar policy específica del tenant
        tenant_policy = self._load_tenant_policy(tenant_id)
        if tenant_policy:
            evaluator = PolicyEvaluator(tenant_policy)
            decision = evaluator.evaluate(action, None, [])
            return decision.effect == "allow"

        # 2. Si no hay policy del tenant, usar la del engine si es del mismo tenant
        if tenant_id == self.tenant_id:
            decision = self.evaluator.evaluate(action, None, [])
            return decision.effect == "allow"

        # 3. Si piden otro tenant y no tiene policy, crear default para ese tenant
        default = default_policy(tenant_id)
        evaluator = PolicyEvaluator(default)
        decision = evaluator.evaluate(action, None, [])

        # En prod, default es deny
        if settings.env!= "dev":
            return False

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
