from __future__ import annotations
from ..beliefs.belief import Belief
class UncertaintyTracker:
    def score(self, belief: Belief) -> float:
        return belief.confidence
