from __future__ import annotations
import re
from typing import Any, Dict, List, Optional

from .action import Action
from .result import ExecutionResult
from ..kernel.policy.engine import PolicyEngine
from ..kernel.world.events import Event
from .tools.registry import ToolRegistry

# Sanitizador de secretos (nunca str(e) crudo)
_SECRET_PATTERNS = [
    r"sk-[a-zA-Z0-9\-_]{20,}",
    r"ya29\.[a-zA-Z0-9\-_]+",
    r"Bearer\s+[a-zA-Z0-9\.\-_]+",
    r"api_key[=:]\s*[a-zA-Z0-9\-_]{10,}",
    r"token[=:]\s*[a-zA-Z0-9\-_]{10,}",
    r"xox[bprs]-[a-zA-Z0-9\-]+",
]


def _safe_error(e: Exception) -> str:
    msg = str(e)
    for pat in _SECRET_PATTERNS:
        msg = re.sub(pat, "[REDACTED_SECRET]", msg, flags=re.IGNORECASE)
    if len(msg) > 300:
        msg = msg[:300] + " [truncated]"
    low = msg.lower()
    if any(k in low for k in ["authorization","credential","secret","private_key"]):
        return "execution failed: provider error (details redacted for security)"
    return msg


from ..kernel.policy.evaluator import Decision


class Executor:
    def __init__(self, registry: Optional[ToolRegistry] = None,
                 policy_engine: Optional[PolicyEngine] = None,
                 event_log: Any = None):
        self.registry = registry or ToolRegistry()
        self.policy = policy_engine or PolicyEngine()
        self.event_log = event_log

    def _audit(self, kind, capability, tenant_id, payload=None,
               actor_id=None, correlation_id=None):
        if self.event_log is None:
            return
        if payload is None:
            payload = {}
        if correlation_id is not None:
            p = dict(payload)
            p["correlation_id"] = correlation_id
            payload = p
        try:
            self.event_log.append(Event(
                kind=kind, entity_id=capability,
                tenant_id=tenant_id or "system",
                actor_id=actor_id or "executor",
                payload=payload))
        except Exception:
            pass

    @staticmethod
    def _tenant_of(context):
        if context is None:
            return None
        if hasattr(context, "tenant"):
            return getattr(context.tenant, "id", None)
        if isinstance(context, dict):
            t = context.get("tenant")
            if isinstance(t, dict):
                return t.get("id")
            if t is not None:
                return getattr(t, "id", None)
        return None

    @staticmethod
    def _params_summary(params):
        try:
            return {k: f"<{type(v).__name__}>"
                    for k, v in sorted(params.items())}
        except Exception:
            return {}

    def _policy_decision(self, action: str, context: Any = None, roles: Optional[List[str]] = None,
                         tenant_id: Optional[str] = None) -> Decision:
        if self.policy is None:
            return Decision(effect="deny", rule_id="policy_required", reason="No policy engine configured (deny-by-default)")
        if tenant_id and tenant_id != "system":
            return self.policy.can_for_tenant(
                tenant_id, action, context, roles)
        return self.policy.can(action, context, roles)

    def execute_action(self, action, roles=None):
        """API legacy: delega a execute()."""
        act = action.value if hasattr(action, "value") else action
        res = self.execute(act, {}, roles=roles)
        return ExecutionResult(action=action,
            success=res.get("success", False),
            output=res.get("output"),
            error=res.get("error"))

    def execute(self, action, params=None, context=None,
                roles=None, tenant_id=None,
                correlation_id=None, actor_id=None,
                **kwargs):
        """API principal: SIEMPRE policy + audita."""
        params = params or {}
        tid = tenant_id or self._tenant_of(context)
        actor = actor_id or (roles[0] if roles else "executor")

        # 0. POLICY - SIEMPRE primero, fail-closed
        decision = self._policy_decision(action, context, roles, tid)
        if decision and decision.effect == "deny":
            self._audit("ActionDenied", action, tid, {
                "reason": f"denied by {decision.rule_id}",
                "params": self._params_summary(params)},
                actor, correlation_id)
            return {"success": False,
                "error": f"denied by {decision.rule_id}",
                "decision": decision.model_dump()}
        if decision and decision.effect == "require_approval":
            self._audit("ApprovalRequired", action, tid, {
                "reason": "approval required",
                "params": self._params_summary(params)},
                actor, correlation_id)
            return {"success": False, "error": "approval required",
                "decision": decision.model_dump()}

        # 1. Buscar la tool
        tool = self.registry.get(action)
        if tool is None:
            self._audit("ToolFailed", action, tid, {
                "status": "error",
                "error": f"tool '{action}' no encontrada"},
                actor, correlation_id)
            return {"success": False,
                "error": f"tool '{action}' no encontrada"}

        # 2. Ejecutar (auditando ciclo completo)
        self._audit("ActionStarted", action, tid, {
            "status": "started",
            "params": self._params_summary(params)},
            actor, correlation_id)
        try:
            output = tool.run(params)
            self._audit("ToolCompleted", action, tid, {
                "status": "ok",
                "output_keys": (sorted(output.keys())
                    if isinstance(output, dict)
                    else "non-dict")},
                actor, correlation_id)
            return {"success": True, "output": output}
        except Exception as e:
            safe = _safe_error(e)
            self._audit("ToolFailed", action, tid, {
                "status": "error", "error": safe},
                actor, correlation_id)
            return {"success": False, "error": safe}