from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from ..beliefs.belief import Belief

class SemanticMemory(BaseModel):
    """Hechos estables upsert por key. Wrapper sobre CognitionStore.semantic_*"""

    model_config = ConfigDict(frozen=False, extra="forbid")

    facts: Dict[str, Any] = Field(default_factory=dict)

    def upsert(self, key: str, value: Any, belief: Optional[Belief] = None) -> None:
        self.facts[key] = {"value": value, "belief_id": belief.id if belief else None}

    def get(self, key: str) -> Optional[Any]:
        entry = self.facts.get(key)
        return entry["value"] if entry else None

    def search(self, query: str) -> List[str]:
        q = query.lower()
        return [k for k in self.facts.keys() if q in k.lower() or q in str(self.facts[k]).lower()]
