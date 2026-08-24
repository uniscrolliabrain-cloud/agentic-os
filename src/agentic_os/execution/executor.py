from __future__ import annotations
from .action import Action
from .result import ExecutionResult
from ..kernel.policy.engine import PolicyEngine
from .tools.registry import ToolRegistry
class Executor:
    def __init__(self, policy_engine: PolicyEngine, tools: ToolRegistry):
        self.policy = policy_engine
        self.tools = tools
    def execute(self, action: Action, roles: List[str]) -> ExecutionResult:
        decision = self.policy.can(action.capability, None, roles)
        if decision.effect == "deny":
            return ExecutionResult(action_id=action.id, success=False, error=f"denied by {decision.rule_id}")
        if decision.effect == "require_approval":
            return ExecutionResult(action_id=action.id, success=False, error="approval required")
        tool = self.tools.get(action.capability)
        if not tool:
            return ExecutionResult(action_id=action.id, success=False, error="tool not found")
        try:
            out = tool.run(action.params)
            return ExecutionResult(action_id=action.id, success=True, output=out)
        except Exception as e:
            return ExecutionResult(action_id=action.id, success=False, error=str(e))
