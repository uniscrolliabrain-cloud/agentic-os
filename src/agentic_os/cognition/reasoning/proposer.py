from __future__ import annotations
from typing import List
from ..beliefs.belief import Belief
from ..planning.intent import Intent
class Proposer:
    """LLM-backed proposer: proposes Intents, never Actions"""
    def propose(self, beliefs: List[Belief], goal: str) -> List[Intent]:
        # deterministic stub - real LLM implements this interface
        return [Intent(goal=goal, rationale="stub")]
