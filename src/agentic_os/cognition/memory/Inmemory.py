"""MemoryStore in-process legado (sin persistencia).

Se mantiene para compatibilidad con tests/kernel/test_registry_memory_contracts
y usos de corta vida. Para memoria persistente por (tenant, agente) usar
CognitionStore (cognition/memory/store.py).
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MemoryItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class MemoryStore:
    """Almacén en proceso, determinista (matching por términos)."""

    def __init__(self) -> None:
        self._items: dict[str, MemoryItem] = {}

    def put(self, item: MemoryItem) -> None:
        if not item.id:
            raise ValueError("MemoryItem.id es obligatorio")
        self._items[item.id] = item

    def get(self, item_id: str) -> MemoryItem | None:
        return self._items.get(item_id)

    def delete(self, item_id: str) -> None:
        self._items.pop(item_id, None)

    def search(self, query: str) -> list[MemoryItem]:
        q = (query or "").strip().lower()
        if not q:
            return []
        terms = q.split()
        scored: list[tuple[int, str, MemoryItem]] = []
        for item in self._items.values():
            haystack = " ".join(
                [item.id, item.content] + [str(v) for v in item.metadata.values()]
            ).lower()
            score = sum(haystack.count(t) for t in terms)
            if score > 0:
                scored.append((score, item.id, item))
        scored.sort(key=lambda t: (-t[0], t[1]))
        return [item for _, _, item in scored]

    def __len__(self) -> int:
        return len(self._items)
