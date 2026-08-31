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

    El allow-all SOLO se activa con DEV_ALLOW_ALL=true (flag explícito, default false).
    ENV=dev por sí solo NO cambia la semántica de seguridad: en ausencia de
    DEV_ALLOW_ALL, la política por defecto es deny-all incluso en dev.

    Nota de seguridad (Fase 1 hardening): antes esto disparaba allow-all
    automáticamente con settings.env == "dev", lo que era un allow-all implícito.
    """
    if _dev_allow_all():
        return Policy(
            id=f"default-{tenant_id}",
            name=f"default-allow-{tenant_id}",
            rules=[
                PolicyRule(
                    id=f"allow-all-{tenant_id}",
                    capability="*",
                    effect="allow",
                    requires_roles=[],
                    description=(
                        f"Default allow SOLO con DEV_ALLOW_ALL=true "
                        f"(tenant {tenant_id}), para desarrollo sin tenants configurados"
                    ),
                )
            ],
        )
    # Sin DEV_ALLOW_ALL: sin reglas = deny by default (también en dev)
    return Policy(
        id=f"default-{tenant_id}",
        name=f"default-deny-{tenant_id}",
        rules=[],
    )

def _dev_allow_all() -> bool:
    """Flag explicito. ENV=dev NO lo activa.
    
    Nota (Fase 1 hardening): esto es el UNICO disparador del allow-all.
    """
    return os.environ.get("DEV_ALLOW_ALL", "false").lower() in ("1", "true", "yes")

class PolicyEngine:
    """Motor de políticas determinista con aislamiento multi-tenant."""

    def __init__(self, policy: Optional[Policy] = None, tenant_id: str = "default"):
        self.tenant_id = tenant_id
        self.policy = policy or default_policy(tenant_id)
        self.evaluator = PolicyEvaluator(self.policy)

    def _get_tenant(self, tenant_id: str):
        """Resuelve el Tenant (para leer enabled_capabilities) o None sin dep fuerte de tenancy."""
        try:
            from ...infrastructure.tenancy import TenantRegistry
            return TenantRegistry().get(tenant_id)
        except Exception:
            return None

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
        # Si la política es allow-all pero sin DEV_ALLOW_ALL, denegar.
        if not _dev_allow_all():
            if any(r.capability == "*" and r.effect == "allow" for r in self.policy.rules):
                return Decision(effect="deny", reason="allow-all sin DEV_ALLOW_ALL")

        return self.evaluator.evaluate(capability, resource_kind, roles or [])

    def is_allowed(self, tenant_id: str, action: str) -> bool:
        """
        AHORA SÍ mira policy del tenant + enabled_capabilities.
        No decide por el engine global de otro tenant.
        """
        # 0. enabled_capabilities del tenant (aislamiento real): si la capability
        # no está habilitada para este tenant, deny — incluso con DEV_ALLOW_ALL.
        tenant = self._get_tenant(tenant_id)
        if tenant is not None:
            enabled = list(tenant.config.enabled_capabilities)
            if enabled and action not in enabled:
                return False
            if not enabled:
                # Sin capabilities habilitadas: deny (el tenant no participa del allow-all)
                return False

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

        # Sin DEV_ALLOW_ALL, default es deny (también en dev)
        if not _dev_allow_all():
            return False

        return decision.effect == "allow"

    def can_for_tenant(
        self,
        tenant_id: str,
        capability: str,
        resource_kind: Optional[str] = None,
        roles: Optional[list[str]] = None,
    ) -> Decision:
        """Evalúa una capability contra la policy del tenant (o default deny).

        Aislamiento multi-tenant real: nunca se usa una regla de un tenant distinto
        para decidir sobre otro, y enabled_capabilities del tenant es parte de la
        decisión: si la capability no está habilitada, deny (incluso con DEV_ALLOW_ALL).
        """
        # 0. enabled_capabilities antes de cualquier otra regla
        tenant = self._get_tenant(tenant_id)
        if tenant is not None:
            enabled = list(tenant.config.enabled_capabilities)
            if enabled and capability not in enabled:
                return Decision(effect="deny", reason=f"{capability} no habilitada para tenant {tenant_id}")
            if not enabled:
                return Decision(effect="deny", reason=f"tenant {tenant_id} sin capabilities habilitadas")

        policy = self._load_tenant_policy(tenant_id)
        if policy is None:
            policy = default_policy(tenant_id)

        # Si la política resultante es allow-all pero sin DEV_ALLOW_ALL, negar.
        if not _dev_allow_all():
            if any(r.capability == "*" and r.effect == "allow" for r in policy.rules):
                return Decision(effect="deny", reason=f"allow-all sin DEV_ALLOW_ALL no permitido para {tenant_id}")

        evaluator = PolicyEvaluator(policy)
        return evaluator.evaluate(capability, resource_kind, roles or [])

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
