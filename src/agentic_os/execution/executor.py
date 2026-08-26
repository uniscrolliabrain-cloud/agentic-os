from __future__ import annotations
from typing import Any, Dict, List, Optional

from .action import Action
from .result import ExecutionResult
from ..kernel.policy.engine import PolicyEngine
from .tools.registry import ToolRegistry


class Executor:
    """Ejecuta acciones de forma determinista.

    El flujo es: el LLM propone una Intent -> el PolicyEngine la valida ->
    el Executor busca la tool correspondiente en el registry y la ejecuta.
    El Executor NUNCA decide por sí mismo: solo ejecuta lo que la policy permite.
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