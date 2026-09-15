from __future__ import annotations
from typing import List, Dict
from collections import defaultdict
from ..beliefs.belief import Belief

class ConsistencyChecker:
    """Detecta contradicciones por misma key con contenido distinto y alta confianza."""

    def check(self, beliefs: List[Belief]) -> List[str]:
        issues: List[str] = []
        by_key: Dict[str, List[Belief]] = defaultdict(list)
        for b in beliefs:
            by_key[b.key].append(b)

        for key, group in by_key.items():
            if len(group) <= 1:
                continue
            # si hay 2 beliefs con misma key pero content distinto y confianza >0.7
            contents = [str(b.content) for b in group]
            if len(set(contents)) > 1:
                high_conf = [b for b in group if b.confidence > 0.7]
                if len(high_conf) >= 2:
                    issues.append(f"CONFLICT key={key!r} con {len(group)} valores distintos alta confianza: {[b.id[:8] for b in high_conf]}")
        return issues

    def resolve(self, beliefs: List[Belief]) -> List[Belief]:
        # keep highest confidence per key
        by_key: Dict[str, Belief] = {}
        for b in beliefs:
            existing = by_key.get(b.key)
            if existing is None or b.confidence > existing.confidence:
                by_key[b.key] = b
        return list(by_key.values())
