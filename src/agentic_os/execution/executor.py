from __future__ import annotations
import re
from typing import Any, Dict, List, Optional

from .action import Action
from .result import ExecutionResult
from ..kernel.policy.engine import PolicyEngine
from ..kernel.world.events import Event
from .tools.registry import ToolRegistry

# --- Sanitizador de secretos (hallazgo de Claude) ---
# Nunca devolver str(e) crudo al frontend
_SECRET_PATTERNS = [
    r"sk-[a-zA-Z0-9\-_]{20,}", # OpenAI
    r"ya29\.[a-zA-Z0-9\-_]+",  # Google
    r"Bearer\s+[a-zA-Z0-9\.\-_]+",
    r"api_key[=:]\s*[a-zA-Z0-9\-_]{10,}",
    r"token[=:]\s*[a-zA-Z0-9\-_]{10,}",
    r"xox[bprs]-[a-zA-Z0-9\-]+",  # Slack
]

def _safe_error(e: Exception) -> str:
    msg = str(e)
    for pat in _SECRET_PATTERNS:
        msg = re.sub(pat, "[REDACTED_SECRET]", msg, flags=re.IGNORECASE)
    if len(msg) > 300:
        msg = msg[:300] + " [truncated]"
    lowered = msg.lower()
    if any(k in lowered for k in ["authorization", "credential", "secret", "private_key"]):
        return "execution failed: provider error (details redacted for security)"
    return msg


class Executor:
    """Ejecuta acciones de forma determinista.

    INVARIANTE 1: NINGUNA ejecución llega a Tool sin pasar por PolicyEngine.
    INVARIANTE 2 (FASE 3.2): toda ejecución queda auditada en el EventLog del
    tenant -> ActionStarted -> (ToolCompleted | ToolFailed | ActionDenied |
    ApprovalRequired). El log se inyecta por constructor (rest.py/producción
    siempre lo pasa; en tests unitarios aislados puede ser None).
    """

    def __init__(self, registry: Optional[ToolRegistry] = None,
                 policy_engine: Optional[PolicyEngine] = None,
                 event_log: Any = None):
        self.registry = registry or ToolRegistry()
        self.policy = policy_engine
        self.event_log = event_log  # EventLogRepository (append-only)

    # ------------------------------------------------------ auditoría -----
    @staticmethod
    def _tenant_of(context: Any) -> Optional[str]:
        if context is not None and hasattr(context, "tenant"):
            return getattr(context.tenant, "id", None)
        return None

    def _audit(self, kind: str, capability: str, tenant_id: Optional[str],
               payload: Dict[str, Any], actor_id: Optional[str] = None) -> None:
        """Emite un evento de auditoría al EventLog del tenant.

        NUNCA lanza (auditar no puede romper la ejecución) y el payload
        nunca contiene secretos: los params se resumen como tipos, nunca
        como valores; los errores pasan por _safe_error().
        """
        if self.event_log is None:
            return
        try:
            self.event_log.append(Event(
                kind=kind,
                entity_id=capability,
                tenant_id=tenant_id or "system",
                actor_id=actor_id or "executor",
                payload=payload,
            ))
        except Exception:  # noqa: BLE001 - auditar jamás rompe el flujo
            pass

    @staticmethod
    def _params_summary(params: Dict[str, Any]) -> Dict[str, str]:
        """Solo nombres de campo + tipo: NUNCA valores (pueden traer secretos)."""
        try:
            return {k: f"<{type(v).__name__}>" for k, v in sorted(params.items())}
        except Exception:  # noqa: BLE001
            return {}

    def _policy_decision(self, action: str, context: Any,
                         roles: Optional[List[str]],
                         tenant_id: Optional[str] = None):
        if not self.policy:
            return None
        tid = tenant_id or self._tenant_of(context)
        if tid:
            return self.policy.can_for_tenant(tid, action, None, roles or [])
        return self.policy.can(action, context, roles or [])

    def execute(self, action: str, params: Dict[str, Any], context: Any = None,
                roles: Optional[List[str]] = None,
                tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Ejecuta una acción (capability). SIEMPRE pasa por policy y
        SIEMPRE deja rastro de auditoría (FASE 3.2).

        `tenant_id` es un kwarg opcional: si no se pasa, se resuelve del
        `context` (TenantContext). Las llamadas existentes no se rompen.
        """
        tid = tenant_id or self._tenant_of(context)
        actor_id = (roles[0] if roles else None)

        # 0. POLICY CHECK - aquí dentro, no en el caller
        decision = self._policy_decision(action, context, roles, tenant_id=tenant_id)
        if decision and decision.effect == "deny":
            self._audit("ActionDenied", action, tid, {
                "reason": f"denied by {decision.rule_id}",
                "params": self._params_summary(params),
            }, actor_id)
            return {"success": False, "error": f"denied by {decision.rule_id}", "decision": decision}
        if decision and decision.effect == "require_approval":
            self._audit("ApprovalRequired", action, tid, {
                "reason": "approval required",
                "params": self._params_summary(params),
            }, actor_id)
            return {"success": False, "error": "approval required", "decision": decision}

        # 1. Buscar la tool
        tool = self.registry.get(action)
        if tool is None:
            self._audit("ToolFailed", action, tid, {
                "status": "error", "error": f"tool '{action}' no encontrada",
            }, actor_id)
            return {"success": False, "error": f"tool '{action}' no encontrada"}

        # 2. Ejecutar la tool de forma determinista (auditando el ciclo)
        self._audit("ActionStarted", action, tid, {
            "status": "started", "params": self._params_summary(params),
        }, actor_id)
        try:
            output = tool.run(params)
            self._audit("ToolCompleted", action, tid, {
                "status": "ok",
                "output_keys": sorted(output.keys()) if isinstance(output, dict) else "non-dict",
            }, actor_id)
            return {"success": True, "output": output}
        except Exception as e:
            safe = _safe_error(e)
            self._audit("ToolFailed", action, tid, {
                "status": "error", "error": safe,
            }, actor_id)
            return {"success": False, "error": safe}

    # --- Compatibilidad con la API anterior (Action-based) ---
    def execute_action(self, action: Action, roles: List[str]) -> ExecutionResult:
        tenant_id = None
        decision = self.policy.can(action.capability, None, roles) if self.policy else None
        if decision and decision.effect == "deny":
            self._audit("ActionDenied", action.capability, tenant_id, {
                "reason": f"denied by {decision.rule_id}",
                "params": self._params_summary(action.params),
            }, roles[0] if roles else None)
            return ExecutionResult(action_id=action.id, success=False, error=f"denied by {decision.rule_id}")
        if decision and decision.effect == "require_approval":
            self._audit("ApprovalRequired", action.capability, tenant_id, {
                "reason": "approval required",
                "params": self._params_summary(action.params),
            }, roles[0] if roles else None)
            return ExecutionResult(action_id=action.id, success=False, error="approval required")
        tool = self.registry.get(action.capability)
        if not tool:
            self._audit("ToolFailed", action.capability, tenant_id, {
                "status": "error", "error": "tool not found",
            }, roles[0] if roles else None)
            return ExecutionResult(action_id=action.id, success=False, error="tool not found")
        self._audit("ActionStarted", action.capability, tenant_id, {
            "status": "started", "params": self._params_summary(action.params),
        }, roles[0] if roles else None)
        try:
            out = tool.run(action.params)
            self._audit("ToolCompleted", action.capability, tenant_id, {
                "status": "ok",
                "output_keys": sorted(out.keys()) if isinstance(out, dict) else "non-dict",
            }, roles[0] if roles else None)
            return ExecutionResult(action_id=action.id, success=True, output=out)
        except Exception as e:
            safe = _safe_error(e)
            self._audit("ToolFailed", action.capability, tenant_id, {
                "status": "error", "error": safe,
            }, roles[0] if roles else None)
            return ExecutionResult(action_id=action.id, success=False, error=safe)