from __future__ import annotations
from typing import List
from ..beliefs.belief import Belief
class ConsistencyChecker:
    def check(self, beliefs: List[Belief]) -> List[str]:
        # returns list of inconsistencies
        return []
