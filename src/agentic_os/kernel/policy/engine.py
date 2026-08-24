from __future__ import annotations
from typing import Optional
from .models import Policy
from .evaluator import PolicyEvaluator, Decision
from .approval import ApprovalRequest
class PolicyEngine:
    def __init__(self, policy: Policy):
        self.policy = policy
        self.evaluator = PolicyEvaluator(policy)
    def can(self, capability: str, resource_kind: Optional[str], roles: list[str]) -> Decision:
        return self.evaluator.evaluate(capability, resource_kind, roles)
    def requires_approval(self, decision: Decision) -> bool:
        return decision.effect == "require_approval"
    def request_approval(self, actor_id: str, capability: str, resource_id: Optional[str] = None) -> ApprovalRequest:
        return ApprovalRequest(actor_id=actor_id, capability=capability, resource_id=resource_id)
