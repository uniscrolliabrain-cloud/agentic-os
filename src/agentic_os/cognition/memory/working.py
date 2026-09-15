from __future__ import annotations
from typing import List
from pydantic import BaseModel, ConfigDict, Field
from ..beliefs.belief import Belief

class WorkingMemory(BaseModel):
    """Hot cache de 7+-2 beliefs activos. Implementacion real sobre CognitionStore."""

    model_config = ConfigDict(frozen=False, extra="forbid")

    beliefs: List[Belief] = Field(default_factory=list)
    capacity: int = Field(default=20, ge=1, le=200)

    def add(self, belief: Belief) -> None:
        # evita duplicados por key, mantiene el de mayor confianza
        existing_idx = next((i for i, b in enumerate(self.beliefs) if b.key == belief.key), None)
        if existing_idx is not None:
            if belief.confidence > self.beliefs[existing_idx].confidence:
                self.beliefs[existing_idx] = belief
        else:
            self.beliefs.append(belief)
        # capado
        if len(self.beliefs) > self.capacity:
            # expulsa menor confianza
            self.beliefs.sort(key=lambda b: b.confidence)
            self.beliefs = self.beliefs[-self.capacity:]

    def get(self, key: str) -> Belief | None:
        for b in self.beliefs:
            if b.key == key:
                return b
        return None

    def all_high_conf(self, threshold: float = 0.7) -> List[Belief]:
        return [b for b in self.beliefs if b.confidence >= threshold]
