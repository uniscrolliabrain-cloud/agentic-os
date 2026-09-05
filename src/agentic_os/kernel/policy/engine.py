from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from .approval import ApprovalRequest
from .evaluator import Decision, PolicyEvaluator
from .models import Policy, PolicyRule
from ..types.ids import new_id


def _dev_allow_all() -> bool:
    return os.environ.get(
        "DEV_ALLOW_ALL",
        "false",
    ).lower() in {
        "1",
        "true",
        "yes",
    }


def default_policy(tenant_id: str = "default") -> Policy:

    if _dev_allow_all():
        return Policy(
            id=f"default-{tenant_id}",
            name=f"default-dev-{tenant_id}",
            rules=[
                PolicyRule(
                    id=f"allow-all-{tenant_id}",
                    capability="*",
                    effect="allow",
                    requires_roles=[],
                    description="DEV ONLY",
                )
            ],
        )

    return Policy(
        id=f"default-{tenant_id}",
        name=f"default-deny-{tenant_id}",
        rules=[],
    )


class PolicyEngine:
    """
    Único punto de decisión de autorización.

    Regla:
        tenant -> capabilities -> policy -> decision

    Ningún caller debe usar una policy global para ejecutar
    una acción perteneciente a un tenant.
    """

    def __init__(
        self,
        policy: Optional[Policy] = None,
        tenant_id: str = "default",
    ):
        self.tenant_id = tenant_id
        self.policy = policy or default_policy(tenant_id)
        # policy inyectada explícitamente (tests/ejecución de tools) se evalúa
        # cuando no hay tenant_id; la default-deny nunca se salta el fail-closed.
        self._has_explicit_policy = policy is not None

    def _tenant(self, tenant_id: str):
        try:
            from ...infrastructure.tenancy import TenantRegistry
            return TenantRegistry().get(tenant_id)
        except Exception:
            return None

    def _load_policy(
        self,
        tenant_id: str,
    ) -> Policy:

        path = Path(
            f"data/policies/{tenant_id}.json"
        )

        if path.exists():
            try:
                return Policy(
                    **json.loads(
                        path.read_text(
                            encoding="utf-8"
                        )
                    )
                )
            except Exception:
                # Policy corrupta = deny.
                return default_policy(tenant_id)

        return default_policy(tenant_id)

    def decide(
        self,
        tenant_id: str,
        capability: str,
        resource_kind: Optional[str] = None,
        roles: Optional[list[str]] = None,
    ) -> Decision:

        if not tenant_id:
            if self._has_explicit_policy:
                return PolicyEvaluator(self.policy).evaluate(
                    capability,
                    resource_kind,
                    roles or [],
                )
            return Decision(
                effect="deny",
                reason="tenant_id obligatorio",
            )

        if tenant_id == "system":
            policy = self._load_policy(tenant_id)
        else:
            tenant = self._tenant(tenant_id)

            if tenant is None:
                # Tenant no registrado: con DEV_ALLOW_ALL=true (dev) se permite
                # (tenants efímeros de tests). Con false (default, producción)
                # siempre deny. DEV_ALLOW_ALL es el ÚNICO gate; ENV=dev no abre.
                if _dev_allow_all():
                    return Decision(
                        effect="allow",
                        reason="DEV_ALLOW_ALL=true",
                    )
                return Decision(
                    effect="deny",
                    reason=(
                        f"policy: tenant "
                        f"'{tenant_id}' no encontrado"
                    ),
                )

            enabled = set(
                tenant.config.enabled_capabilities
            )

            if capability not in enabled:
                return Decision(
                    effect="deny",
                    reason=(
                        f"capability '{capability}' "
                        f"no habilitada para tenant "
                        f"'{tenant_id}'"
                    ),
                )

            if _dev_allow_all():
                return Decision(
                    effect="allow",
                    reason="DEV_ALLOW_ALL=true",
                )

            policy = self._load_policy(tenant_id)

        if (
            not _dev_allow_all()
            and any(
                rule.capability == "*"
                and rule.effect == "allow"
                for rule in policy.rules
            )
        ):
            return Decision(
                effect="deny",
                reason="allow-all requiere DEV_ALLOW_ALL=true",
            )

        evaluator = PolicyEvaluator(policy)

        return evaluator.evaluate(
            capability,
            resource_kind,
            roles or [],
        )

    def can_for_tenant(
        self,
        tenant_id: str,
        capability: str,
        resource_kind: Optional[str] = None,
        roles: Optional[list[str]] = None,
    ) -> Decision:

        return self.decide(
            tenant_id=tenant_id,
            capability=capability,
            resource_kind=resource_kind,
            roles=roles,
        )

    def is_allowed(
        self,
        tenant_id: str,
        action: str,
    ) -> bool:

        return (
            self.decide(
                tenant_id,
                action,
            ).effect
            == "allow"
        )

    def requires_approval(
        self,
        decision: Decision,
    ) -> bool:
        return decision.effect == "require_approval"

    def request_approval(
        self,
        actor_id: str,
        capability: str,
        resource_id: Optional[str] = None,
    ) -> ApprovalRequest:

        return ApprovalRequest(
            id=new_id(),
            actor_id=actor_id,
            capability=capability,
            resource_id=resource_id,
        )
