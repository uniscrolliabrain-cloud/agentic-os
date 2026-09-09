from __future__ import annotations

from typing import List, Tuple

from .store import MemoryItem, MemoryStore

PROMPT_SKILLS_K = 3


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


def retrieve_prompt_skills(
    store: MemoryStore,
    query: str,
    tenant_id: str,
    k: int = PROMPT_SKILLS_K,
) -> List[Tuple[MemoryItem, int]]:
    """Divulgación progresiva: top-k Prompt Skills del tenant, ordenados por
    magnetismo determinista (ya los ordena ``MemoryStore.search``).

    Devuelve ``(MemoryItem, score)`` con ``score`` = magnetismo calculado por
    ``MemoryStore.score``. Aislamiento por tenant: solo se consideran ítems
    con ``metadata['tenant_id'] == tenant_id`` (nunca se filtran en el caller).
    """
    if k <= 0:
        return []
    candidates = [
        item
        for item in store.search(query)
        if item.metadata.get("tenant_id") == tenant_id
    ]
    return [
        (item, store.score(query, item))
        for item in candidates[:k]
    ]

