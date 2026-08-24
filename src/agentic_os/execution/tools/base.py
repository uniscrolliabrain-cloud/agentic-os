from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict
from pydantic import BaseModel


class Tool(ABC):
    name: str
    capability: str

    @abstractmethod
    def run(self, params: Dict[str, Any] | BaseModel) -> Dict[str, Any]: ...

