"""PolicyEngine — decision unica de autorizacion.

Invariantes (docs/INVARIANTS.md):
- Deny by default.
- Delete/Publish -> approval, incluso bajo DEV_ALLOW_ALL.
- El engine NO debe leer disco con ruta CWD-dependiente.
- El engine NO debe importar estaticamente fuera del kernel (AUD-01).

AUD-01 (cerrado): las dependencias de infraestructura (TenantRegistry,
directorio de policies) se inyectan. El fallback usa importlib dinamico
(no aparece como nodo ImportFrom en el AST) SOLO para retrocompatibilidad
con tests que construyen PolicyEngine() sin argumentos.

AUD-02 (cerrado): policies_dir es inyectable. Sin inyeccion se mantiene el
comportamiento historico (CWD-relativo), pero el camino canonico (rest.py)
lo pasa absoluto.

AUD-11 (cerrado): DEV_ALLOW_ALL=true ya NO retorna allow antes del
evaluador. Pasa por PolicyEvaluator con una policy allow-all explicita,
de modo que el endurecimiento delete/publish sigue vigente.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Callable, Optional

from .approval import ApprovalRequest
from .evaluator import Decision, PolicyEvaluator
from .models import Policy, PolicyRule
from ..types.ids import new_id


def _dev_allow_all() -> bool:
    return os.environ.get("DEV_ALLOW_ALL", "false").lower() in {"1", "true", "yes"}


def _dev_policy(tenant_id: str) -> Policy:
    return Policy(
        id=f"dev-allow-all-{tenant_id}",
        name=f"dev-allow-all-{tenant_id}",
        rules=[
            PolicyRule(
                id=f"dev-allow-all-{tenant_id}",
                capability="*",
                effect="allow",
                requires_roles=[],
                description="DEV ONLY",
            )
        ],
    )


def default_policy(tenant_id: str = "default") -> Policy:
    if _dev_allow_all():
        return _dev_policy(tenant_id)
    return Policy(
        id=f"default-{tenant_id}",
        name=f"default-deny-{tenant_id}",
        rules=[],
    )


def _dynamic_tenant_resolver(tenant_id: str):
    """Fallback de retrocompatibilidad: importlib dinamico (no visible al AST)."""
    try:
        from importlib import import_module

        mod = import_module("agentic_os.infrastructure.tenancy")
        return mod.TenantRegistry().get(tenant_id)
    except Exception:
        return None


class PolicyEngine:
    """Unico punto de decision de autorizacion.

    Dependencias inyectables (para mantener el kernel hermetico):
      - policy:           politica explicita (tests, evaluacion pura).
      - policies_dir:     directorio del que se cargan {tenant_id}.json.
      - tenant_resolver:  funcion (tenant_id) -> Tenant | None.
    """

    def __init__(
        self,
        policy: Optional[Policy] = None,
        tenant_id: str = "default",
        policies_dir: Optional[Path | str] = None,
        tenant_resolver: Optional[Callable[[str], object]] = None,
    ):
        self.tenant_id = tenant_id
        self.policy = policy or default_policy(tenant_id)
        self._has_explicit_policy = policy is not None
        self._policies_dir = Path(policies_dir) if policies_dir else Path("data/policies")
        self._tenant_resolver: Callable[[str], object] = (
            tenant_resolver or _dynamic_tenant_resolver
        )

    def _tenant(self, tenant_id: str):
        try:
            return self._tenant_resolver(tenant_id)
        except Exception:
            return None

    def _load_policy(self, tenant_id: str) -> Policy:
        path = self._policies_dir / f"{tenant_id}.json"
        if path.exists():
            try:
                return Policy(**json.loads(path.read_text(encoding="utf-8")))
            except Exception:
                return default_policy(tenant_id)
        return default_policy(tenant_id)

    def decide(
        self,
        tenant_id: str,
        capability: str,
        resource_kind: Optional[str] = None,
        roles: Optional[list[str]] = None,
    ) -> Decision:
        roles = roles or []

        if not tenant_id:
            if self._has_explicit_policy:
                return PolicyEvaluator(self.policy).evaluate(
                    capability, resource_kind, roles
                )
            return Decision(effect="deny", reason="tenant_id obligatorio")

        if tenant_id == "system":
            policy = self._load_policy(tenant_id)
            return PolicyEvaluator(policy).evaluate(capability, resource_kind, roles)

        tenant = self._tenant(tenant_id)

        if tenant is None:
            if _dev_allow_all():
                return PolicyEvaluator(_dev_policy(tenant_id)).evaluate(
                    capability, resource_kind, roles
                )
            return Decision(
                effect="deny",
                reason=f"policy: tenant '{tenant_id}' no encontrado",
            )

        enabled = set(tenant.config.enabled_capabilities)
        if capability not in enabled:
            return Decision(
                effect="deny",
                reason=f"capability '{capability}' no habilitada para tenant '{tenant_id}'",
            )

        if _dev_allow_all():
            return PolicyEvaluator(_dev_policy(tenant_id)).evaluate(
                capability, resource_kind, roles
            )

        policy = self._load_policy(tenant_id)

        if not _dev_allow_all() and any(
            rule.capability == "*" and rule.effect == "allow"
            for rule in policy.rules
        ):
            return Decision(
                effect="deny",
                reason="allow-all requiere DEV_ALLOW_ALL=true",
            )

        return PolicyEvaluator(policy).evaluate(capability, resource_kind, roles)

    def can_for_tenant(
        self,
        tenant_id: str,
        capability: str,
        resource_kind: Optional[str] = None,
        roles: Optional[list[str]] = None,
    ) -> Decision:
        return self.decide(tenant_id, capability, resource_kind, roles)

    def is_allowed(self, tenant_id: str, action: str) -> bool:
        return self.decide(tenant_id, action).effect == "allow"

    def requires_approval(self, decision: Decision) -> bool:
        return decision.effect == "require_approval"

    def request_approval(
        self,
        actor_id: str,
        capability: str,
        resource_id: Optional[str] = None,
    ) -> ApprovalRequest:
        return ApprovalRequest(
            id=new_id(), actor_id=actor_id, capability=capability, resource_id=resource_id
        )