from __future__ import annotations
from typing import List
from .inmemory import MemoryItem, MemoryStore
from .store import CognitionStore
from .models import SemanticFact, WorkingItem

class Retriever:
    def __init__(self, store: MemoryStore):
        self.store = store
    def retrieve(self, query: str, k: int = 5) -> List[MemoryItem]:
        if k <= 0:
            return []
        return self.store.search(query)[:k]

class CognitionRetriever:
    def __init__(self, cog_store: CognitionStore):
        self.cog = cog_store
    def retrieve_working(self, query: str, k: int = 5) -> List[WorkingItem]:
        q = (query or "").lower()
        if not q:
            return self.cog.working_recent(k)
        terms = q.split()
        scored = []
        for item in self.cog.working_recent(200):
            hay = item.content.lower()
            score = sum(hay.count(t) for t in terms)
            if score > 0:
                scored.append((score, item.id, item))
        scored.sort(key=lambda t: (-t[0], t[1]))
        return [i for _,_,i in scored[:k]]
    def retrieve_semantic(self, query: str, k: int = 5) -> List[SemanticFact]:
        return self.cog.semantic_search(query)[:k]
    def retrieve_context(self, query: str, k: int = 5) -> dict:
        return self.cog.context(query=query, k=k)
