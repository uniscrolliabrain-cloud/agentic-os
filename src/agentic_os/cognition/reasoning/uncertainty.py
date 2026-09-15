from __future__ import annotations
from typing import List
from ..beliefs.belief import Belief

class UncertaintyTracker:
    """Tracking de incertidumbre: score + calibracion + decay."""

    def score(self, belief: Belief) -> float:
        # 1 - confidence = incertidumbre base, penaliza si expira pronto o tiene contradicciones
        base = 1.0 - belief.confidence
        if belief.contradicts:
            base += 0.1 * len(belief.contradicts)
        if belief.is_expired():
            return 1.0
        return min(1.0, base)

    def needs_review(self, belief: Belief, threshold: float = 0.4) -> bool:
        return self.score(belief) > threshold

    def aggregate_confidence(self, beliefs: List[Belief]) -> float:
        if not beliefs:
            return 0.0
        # promedio ponderado inverso a incertidumbre
        total = 0.0
        weight_sum = 0.0
        for b in beliefs:
            w = 1.0 - self.score(b) + 0.01
            total += b.confidence * w
            weight_sum += w
        return total / weight_sum if weight_sum else 0.0
