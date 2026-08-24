from __future__ import annotations
from pydantic import BaseModel, ConfigDict
from typing import Optional, Literal
from .models import Effect
class Decision(BaseModel):
    model_config = ConfigDict(frozen=True)
    effect: Effect
    rule_id: Optional[str] = None
    reason: str = ""
class PolicyEvaluator:
    def __init__(self, policy):
        self.policy = policy
    def evaluate(self, capability: str, resource_kind: Optional[str], roles: list[str]) -> Decision:
        for rule in self.policy.rules:
            if rule.capability != capability: continue
            if rule.resource_kind and rule.resource_kind != resource_kind: continue
            if rule.requires_roles and not any(r in roles for r in rule.requires_roles): continue
            return Decision(effect=rule.effect, rule_id=rule.id, reason=rule.description)
        return Decision(effect="deny", reason="no matching rule")
