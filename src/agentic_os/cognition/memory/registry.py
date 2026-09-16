from __future__ import annotations
from pathlib import Path
from typing import Dict, Tuple
from .store import CognitionStore

class CognitionRegistry:
    _instance: "CognitionRegistry | None" = None
    def __new__(cls, base_dir: Path | str = Path("data")):
        if cls._instance is None:
            inst = super().__new__(cls)
            inst._base_dir = Path(base_dir)
            inst._cache: Dict[Tuple[str,str], CognitionStore] = {}
            cls._instance = inst
        return cls._instance
    def __init__(self, base_dir: Path | str = Path("data")):
        pass
    def for_agent(self, tenant_id: str, agent_id: str) -> CognitionStore:
        key = (tenant_id, agent_id)
        if key not in self._cache:
            self._cache[key] = CognitionStore(tenant_id, agent_id, self._base_dir)
        return self._cache[key]
    def clear(self) -> None:
        self._cache.clear()
    @classmethod
    def _reset_singleton(cls) -> None:
        cls._instance = None
