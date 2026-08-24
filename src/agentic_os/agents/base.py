from __future__ import annotations
from abc import ABC, abstractmethod
class BaseAgent(ABC):
    id: str
    @abstractmethod
    def act(self, state): ...
