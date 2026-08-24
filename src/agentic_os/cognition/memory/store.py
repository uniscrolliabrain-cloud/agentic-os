from __future__ import annotations
from typing import Any, Dict
class MemoryStore:
    def __init__(self): self._store: Dict[str, Any] = {}
    def put(self, key: str, value: Any): self._store[key]=value
    def get(self, key: str): return self._store.get(key)
