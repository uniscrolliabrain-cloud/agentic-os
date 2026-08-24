from __future__ import annotations
from abc import ABC, abstractmethod
class Tool(ABC):
    name: str
    @abstractmethod
    def run(self, params: dict) -> dict: ...
