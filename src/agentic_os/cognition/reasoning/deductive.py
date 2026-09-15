from __future__ import annotations
from typing import List, Dict
from ..beliefs.belief import Belief, BeliefKind
from ...kernel.types.ids import new_id

class DeductiveReasoner:
    """Forward chaining simple: si A y A->B entonces B. No inventa hechos."""

    def __init__(self, rules: List[Dict] = None):
        self.rules = rules or []

    def infer(self, beliefs: List[Belief]) -> List[Belief]:
        # 1. index por key
        by_key: Dict[str, Belief] = {b.key: b for b in beliefs}
        new_beliefs: List[Belief] = []

        # Regla de ejemplo: si cliente.email existe -> cliente.contactable = true
        if "cliente.email" in by_key:
            email_belief = by_key["cliente.email"]
            if "cliente.contactable" not in by_key:
                new_beliefs.append(
                    Belief(
                        id=new_id(),
                        kind=BeliefKind.INFERRED,
                        key="cliente.contactable",
                        content={"value": True, "via": "cliente.email existe"},
                        confidence=email_belief.confidence * 0.9,
                        source_observation_id=email_belief.source_observation_id,
                        supports=[email_belief.id],
                    )
                )

        # Reglas custom pasadas en __init__
        for rule in self.rules:
            # rule = {"if_keys": ["a","b"], "then_key": "c", "then_content": {...}}
            if_keys = rule.get("if_keys", [])
            if all(k in by_key for k in if_keys):
                then_key = rule.get("then_key")
                if then_key not in by_key:
                    support_ids = [by_key[k].id for k in if_keys]
                    avg_conf = sum(by_key[k].confidence for k in if_keys) / len(if_keys) if if_keys else 1.0
                    new_beliefs.append(
                        Belief(
                            key=then_key,
                            kind=BeliefKind.INFERRED,
                            content=rule.get("then_content", {}),
                            confidence=avg_conf * rule.get("confidence_factor", 0.9),
                            supports=support_ids,
                        )
                    )

        return beliefs + new_beliefs
