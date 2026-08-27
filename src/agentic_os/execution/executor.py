from __future__ import annotations
import re
from typing import Any, Dict, List, Optional

from.action import Action
from.result import ExecutionResult
from..kernel.policy.engine import PolicyEngine
from.tools.registry import ToolRegistry

# --- Sanitizador de secretos (hallazgo de Claude) ---
# Nunca devolver str(e) crudo al frontend
_SECRET_PATTERNS = [
    r"sk-[a-zA-Z0-9\-_]{20,}", # OpenAI
    r"ya29\.[a-zA-Z0-9\-_]+", # Google
    r"Bearer\s+[a-zA-Z0-9\.\-_]+",
    r"api_key[=:]\s*[a-zA-Z0-9\-_]{10,}",
    r"token[=:]\s*[a-zA-Z0-9\-_]{10,}",
    r"xox[bprs]-[a-zA-Z0-9\-]+", # Slack
]

def _safe_error(e: Exception) -> str:
    msg = str(e)
    # 1. Ocultar secretos conocidos
    for pat in _SECRET_PATTERNS:
        msg = re.sub(pat, "[REDACTED_SECRET]", msg, flags=re.IGNORECASE)
    # 2. Si el mensaje es muy largo, truncar (evita dump de headers)
    if len(msg) > 300:
        msg = msg[:300] + " [truncated]"
    # 3. Mensaje genérico si parece contener credencial
    lowered = msg.lower()
    if any(k in lowered for k in ["authorization", "credential", "secret", "private_key"]):
        return "execution failed: provider error (details redacted for security)"
    return msg

class Executor:
    """Ejecuta acciones de forma determinista.

    INVARIANTE: NINGUNA ejecución llega a Tool sin pasar por PolicyEngine.can()
    El enforcement vive AQUÍ dentro, no en el caller (rest.py, orchestrator, etc).
    """

    def __init__(self, registry: Optional[ToolRegistry] = None, policy_engine: Optional[PolicyEngine] = None):
        self.registry = registry or ToolRegistry()
        self.policy = policy_engine

    def execute(
        self,
        action: str,
        params: Dict[str, Any],
        context: Any = None,
        roles: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Ejecuta una acción (capability) con los parámetros dados.

        - action: nombre de la capability/tool (ej. "gmail_send")
        - params: dict de parámetros para la tool
        - context: TenantContext (para aislamiento multi-tenant)
        - roles: roles del actor (para validación de policy)
        """
        # 0. POLICY CHECK - AQUÍ DENTRO, no en el caller
        # Si hay policy_engine, SIEMPRE preguntar
        if self.policy:
            decision = self.policy.can(action, context, roles or [])
            if decision and decision.effect == "deny":
                return {"success": False, "error": f"denied by {decision.rule_id}", "decision": decision}
            if decision and decision.effect == "require_approval":
                return {"success": False, "error": "approval required", "decision": decision}

        # 1. Buscar la tool
        tool = self.registry.get(action)
        if tool is None:
            return {"success": False, "error": f"tool '{action}' no encontrada"}

        # 2. Ejecutar la tool de forma determinista
        try:
            output = tool.run(params)
            return {"success": True, "output": output}
        except Exception as e:
            return {"success": False, "error": _safe_error(e)}

    # --- Compatibilidad con la API anterior (Action-based) ---
    def execute_action(self, action: Action, roles: List[str]) -> ExecutionResult:
        # Este método ya tenía policy, lo mantenemos pero usando _safe_error
        decision = self.policy.can(action.capability, None, roles) if self.policy else None
        if decision and decision.effect == "deny":
            return ExecutionResult(action_id=action.id, success=False, error=f"denied by {decision.rule_id}")
        if decision and decision.effect == "require_approval":
            return ExecutionResult(action_id=action.id, success=False, error="approval required")
        tool = self.registry.get(action.capability)
        if not tool:
            return ExecutionResult(action_id=action.id, success=False, error="tool not found")
        try:
            out = tool.run(action.params)
            return ExecutionResult(action_id=action.id, success=True, output=out)
        except Exception as e:
            return ExecutionResult(action_id=action.id, success=False, error=_safe_error(e))
        params: Dict[str, Any],
        context: Any = None,
        roles: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Ejecuta una acción (capability) con los parámetros dados.

        - action: nombre de la capability/tool (ej. "gmail_send")
        - params: dict de parámetros para la tool
        - context: TenantContext opcional (para aislamiento multi-tenant)
        - roles: roles del actor (para validación de policy)
        """
        # 1. Buscar la tool
        tool = self.registry.get(action)
        if tool is None:
            return {"success": False, "error": f"tool '{action}' no encontrada"}

        # 2. Ejecutar la tool de forma determinista
        try:
            output = tool.run(params)
            return {"success": True, "output": output}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # --- Compatibilidad con la API anterior (Action-based) ---
    def execute_action(self, action: Action, roles: List[str]) -> ExecutionResult:
        decision = self.policy.can(action.capability, None, roles) if self.policy else None
        if decision and decision.effect == "deny":
            return ExecutionResult(action_id=action.id, success=False, error=f"denied by {decision.rule_id}")
        if decision and decision.effect == "require_approval":
            return ExecutionResult(action_id=action.id, success=False, error="approval required")
        tool = self.registry.get(action.capability)
        if not tool:
            return ExecutionResult(action_id=action.id, success=False, error="tool not found")
        try:
            out = tool.run(action.params)
            return ExecutionResult(action_id=action.id, success=True, output=out)
        except Exception as e:
            return ExecutionResult(action_id=action.id, success=False, error=str(e))
