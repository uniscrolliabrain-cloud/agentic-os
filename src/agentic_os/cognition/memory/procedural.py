from __future__ import annotations
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

class ProceduralMemory(BaseModel):
    """SOPs/skills del agente. Wrapper sobre CognitionStore.procedural_*"""

    model_config = ConfigDict(frozen=False, extra="forbid")

    skills: Dict[str, dict] = Field(default_factory=dict)

    def register(self, name: str, steps: List[dict], description: str = "") -> None:
        self.skills[name] = {"name": name, "description": description, "steps": steps}

    def get(self, name: str) -> Optional[dict]:
        return self.skills.get(name)

    def list(self) -> List[dict]:
        return list(self.skills.values())
