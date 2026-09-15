from __future__ import annotations
from typing import Dict, List, Optional
from collections import defaultdict, deque

class CausalReasoner:
    """Grafo causal simple para explain(event_id)."""

    def __init__(self):
        self._causes: Dict[str, List[str]] = defaultdict(list)  # event_id -> [cause_ids]
        self._effects: Dict[str, List[str]] = defaultdict(list)

    def add_causation(self, cause_id: str, effect_id: str) -> None:
        if effect_id not in self._causes or cause_id not in self._causes[effect_id]:
            self._causes[effect_id].append(cause_id)
        if cause_id not in self._effects or effect_id not in self._effects[cause_id]:
            self._effects[cause_id].append(effect_id)

    def explain(self, event_id: str, depth: int = 3) -> dict:
        # BFS hacia atras
        chain: List[List[str]] = []
        visited = set()
        queue = deque([(event_id, 0, [event_id])])
        while queue:
            cur, d, path = queue.popleft()
            if d >= depth:
                continue
            for cause in self._causes.get(cur, []):
                if cause in visited:
                    continue
                visited.add(cause)
                new_path = [cause] + path
                chain.append(new_path)
                queue.append((cause, d + 1, new_path))
        return {"event_id": event_id, "causal_chains": chain, "direct_causes": self._causes.get(event_id, []), "direct_effects": self._effects.get(event_id, [])}
