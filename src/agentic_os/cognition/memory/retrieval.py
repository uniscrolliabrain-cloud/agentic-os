from __future__ import annotations

from .store import MemoryItem, MemoryStore


class Retriever:
    """Recuperación determinista sobre ``MemoryStore`` (sin embeddings).

    Implementación mínima real: delega en ``MemoryStore.search``
    (matching por términos) y limita a ``k`` resultados. Ya no devuelve
    ``[]`` silenciosamente cuando hay coincidencias disponibles.
    """

    def __init__(self, store: MemoryStore) -> None:
        self.store = store

    def retrieve(self, query: str, k: int = 5) -> list[MemoryItem]:
        if k <= 0:
            return []
        return self.store.search(query)[:k]

