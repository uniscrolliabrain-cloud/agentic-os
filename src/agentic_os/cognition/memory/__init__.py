"""cognition.memory: memorias episodica, semantica, procedural y de trabajo.

Compatibilidad:
- Si inmemory.py existe -> usa MemoryItem/MemoryStore legacy de ahi
- Si no existe (repo viejo) -> fallback a store.py legacy para no romper tests
"""
# Legacy in-memory (intenta inmemory primero, fallback a store legacy si es necesario)
try:
    from .inmemory import MemoryItem, MemoryStore
except ModuleNotFoundError:
    # Fallback: tu store.py original era el MemoryStore viejo
    try:
        from .store import MemoryItem as _MI, MemoryStore as _MS  # type: ignore
        # Si store.py ya es CognitionStore, estos no existiran, entonces importara desde otro lado
        MemoryItem = _MI
        MemoryStore = _MS
    except (ImportError, AttributeError):
        # Ultimo fallback: define aqui mismo para que los tests no rompan
        from pydantic import BaseModel, ConfigDict, Field
        from typing import Any

        class MemoryItem(BaseModel):  # type: ignore[no-redef]
            model_config = ConfigDict(frozen=True)
            id: str
            content: str
            metadata: dict[str, Any] = Field(default_factory=dict)

        class MemoryStore:  # type: ignore[no-redef]
            def __init__(self) -> None:
                self._items: dict[str, MemoryItem] = {}
            def put(self, item: MemoryItem) -> None:
                if not item.id:
                    raise ValueError("MemoryItem.id es obligatorio")
                self._items[item.id] = item
            def get(self, item_id: str):
                return self._items.get(item_id)
            def delete(self, item_id: str) -> None:
                self._items.pop(item_id, None)
            def search(self, query: str):
                q = (query or "").strip().lower()
                if not q:
                    return []
                terms = q.split()
                scored = []
                for item in self._items.values():
                    haystack = " ".join([item.id, item.content] + [str(v) for v in item.metadata.values()]).lower()
                    score = sum(haystack.count(t) for t in terms)
                    if score > 0:
                        scored.append((score, item.id, item))
                scored.sort(key=lambda t: (-t[0], t[1]))
                return [i for _, _, i in scored]
            def __len__(self):
                return len(self._items)

# Persistente por (tenant, agente) - nuevo
try:
    from .models import EpisodicEvent, ProceduralSkill, SemanticFact, WorkingItem
except ImportError:
    EpisodicEvent = ProceduralSkill = SemanticFact = WorkingItem = None  # type: ignore

try:
    from .registry import CognitionRegistry
except ImportError:
    CognitionRegistry = None  # type: ignore

try:
    from .store import CognitionStore, CognitionStoreError
except ImportError:
    # Si store.py es aun el legacy, CognitionStore no existe aun
    CognitionStore = None  # type: ignore
    CognitionStoreError = Exception  # type: ignore

try:
    from .retrieval import Retriever
except ImportError:
    Retriever = None  # type: ignore

__all__ = [
    "MemoryItem",
    "MemoryStore",
    "CognitionStore",
    "CognitionStoreError",
    "CognitionRegistry",
    "WorkingItem",
    "EpisodicEvent",
    "SemanticFact",
    "ProceduralSkill",
    "Retriever",
]
