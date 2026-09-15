"""cognition.memory.store: CognitionStore persistente por (tenant, agente)."""
from __future__ import annotations
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from .models import EpisodicEvent, ProceduralSkill, SemanticFact, WorkingItem
from ...kernel.types.ids import new_id
from ...kernel.types.time import now_utc

class CognitionStoreError(Exception):
    pass

_TENANT_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,127}$")
_AGENT_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,127}$")

def _validate_id(kind: str, value: str, pattern: re.Pattern) -> str:
    if not isinstance(value, str) or not value:
        raise CognitionStoreError(f"{kind} vacio o no str")
    if not pattern.match(value):
        raise CognitionStoreError(f"{kind} invalido {value!r}: debe matchear {pattern.pattern}")
    if ".." in value or "/" in value or "\\" in value:
        raise CognitionStoreError(f"{kind} invalido por traversal: {value!r}")
    return value

def _read_jsonl(path: Path) -> List[dict]:
    if not path.exists():
        return []
    out = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except:
                continue
    return out

def _append_jsonl(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False, default=str) + "\n")

def _rewrite_jsonl(path: Path, objs: List[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for o in objs:
            f.write(json.dumps(o, ensure_ascii=False, default=str) + "\n")

class CognitionStore:
    MAX_WORKING = 200
    def __init__(self, tenant_id: str, agent_id: str, base_dir: Path | str = Path("data")):
        self.tenant_id = _validate_id("tenant_id", tenant_id, _TENANT_RE)
        self.agent_id = _validate_id("agent_id", agent_id, _AGENT_RE)
        self.base_dir = Path(base_dir)
        self._mem_dir = self.base_dir / "tenants" / self.tenant_id / "agents" / self.agent_id / "memory"
        self._mem_dir.mkdir(parents=True, exist_ok=True)
        self._working_cache: Optional[List[WorkingItem]] = None
        self._semantic_cache: Optional[Dict[str, SemanticFact]] = None
        self._procedural_cache: Optional[Dict[str, ProceduralSkill]] = None

    def _p(self, name: str) -> Path:
        return self._mem_dir / f"{name}.jsonl"

    def _load_working(self) -> List[WorkingItem]:
        if self._working_cache is not None:
            return self._working_cache
        rows = _read_jsonl(self._p("working"))
        items = [WorkingItem(**r) for r in rows]
        if len(items) > self.MAX_WORKING:
            items = items[-self.MAX_WORKING:]
        self._working_cache = items
        return items

    def working_add(self, content: str, metadata: Dict[str, Any] = None) -> WorkingItem:
        if not content or not content.strip():
            raise CognitionStoreError("working content vacio")
        item = WorkingItem(tenant_id=self.tenant_id, agent_id=self.agent_id, content=content.strip(), metadata=metadata or {})
        _append_jsonl(self._p("working"), item.model_dump())
        cache = self._load_working()
        cache.append(item)
        if len(cache) > self.MAX_WORKING:
            cache = cache[-self.MAX_WORKING:]
            _rewrite_jsonl(self._p("working"), [c.model_dump() for c in cache])
        self._working_cache = cache
        return item

    def working_recent(self, k: int = 10) -> List[WorkingItem]:
        if k <= 0:
            return []
        return self._load_working()[-k:]

    def working_clear(self) -> None:
        _rewrite_jsonl(self._p("working"), [])
        self._working_cache = []

    def episodic_append(self, event_type: str, payload: Dict[str, Any] = None, correlation_id: str = None) -> EpisodicEvent:
        if not event_type or not event_type.strip():
            raise CognitionStoreError("episodic event_type vacio")
        ev = EpisodicEvent(tenant_id=self.tenant_id, agent_id=self.agent_id, event_type=event_type.strip(), payload=payload or {}, correlation_id=correlation_id)
        _append_jsonl(self._p("episodic"), ev.model_dump())
        return ev

    def episodic_replay(self, event_type: str = None) -> List[EpisodicEvent]:
        rows = _read_jsonl(self._p("episodic"))
        events = [EpisodicEvent(**r) for r in rows]
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        return events

    def episodic_since_minutes(self, minutes: int) -> List[EpisodicEvent]:
        if minutes <= 0:
            return []
        from datetime import timedelta
        cutoff = now_utc() - timedelta(minutes=minutes)
        return [e for e in self.episodic_replay() if e.created_at >= cutoff]

    def _load_semantic(self) -> Dict[str, SemanticFact]:
        if self._semantic_cache is not None:
            return self._semantic_cache
        rows = _read_jsonl(self._p("semantic"))
        cache: Dict[str, SemanticFact] = {}
        for r in rows:
            try:
                fact = SemanticFact(**r)
                cache[fact.key] = fact
            except:
                continue
        self._semantic_cache = cache
        return cache

    def semantic_upsert(self, key: str, value: Any, source_belief_id: str = None, confidence: float = 1.0) -> SemanticFact:
        if not key or not key.strip():
            raise CognitionStoreError("semantic key vacia")
        key = key.strip()
        cache = self._load_semantic()
        now = now_utc()
        existing = cache.get(key)
        fact = SemanticFact(id=existing.id if existing else new_id(), tenant_id=self.tenant_id, agent_id=self.agent_id, key=key, value=value, source_belief_id=source_belief_id, confidence=confidence, created_at=existing.created_at if existing else now, updated_at=now)
        cache[key] = fact
        _rewrite_jsonl(self._p("semantic"), [f.model_dump() for f in cache.values()])
        self._semantic_cache = cache
        return fact

    def semantic_get(self, key: str) -> Optional[SemanticFact]:
        return self._load_semantic().get(key)

    def semantic_all(self) -> List[SemanticFact]:
        return list(self._load_semantic().values())

    def semantic_search(self, query: str) -> List[SemanticFact]:
        q = (query or "").lower()
        if not q:
            return []
        terms = q.split()
        scored = []
        for fact in self._load_semantic().values():
            hay = f"{fact.key} {str(fact.value)}".lower()
            score = sum(hay.count(t) for t in terms)
            if score > 0:
                scored.append((score, fact.key, fact))
        scored.sort(key=lambda t: (-t[0], t[1]))
        return [f for _,_,f in scored]

    def _load_procedural(self) -> Dict[str, ProceduralSkill]:
        if self._procedural_cache is not None:
            return self._procedural_cache
        rows = _read_jsonl(self._p("procedural"))
        cache: Dict[str, ProceduralSkill] = {}
        for r in rows:
            try:
                skill = ProceduralSkill(**r)
                cache[skill.name] = skill
            except:
                continue
        self._procedural_cache = cache
        return cache

    def procedural_register(self, name: str, description: str = "", steps: List[Dict[str, Any]] = None, version: int = None) -> ProceduralSkill:
        if not name or not name.strip():
            raise CognitionStoreError("procedural name vacio")
        name = name.strip()
        cache = self._load_procedural()
        now = now_utc()
        existing = cache.get(name)
        skill = ProceduralSkill(id=existing.id if existing else new_id(), tenant_id=self.tenant_id, agent_id=self.agent_id, name=name, description=description, steps=steps or [], version=version if version is not None else (existing.version + 1 if existing else 1), created_at=existing.created_at if existing else now, updated_at=now)
        cache[name] = skill
        _rewrite_jsonl(self._p("procedural"), [s.model_dump() for s in cache.values()])
        self._procedural_cache = cache
        return skill

    def procedural_get(self, name: str) -> Optional[ProceduralSkill]:
        return self._load_procedural().get(name)

    def procedural_list(self) -> List[ProceduralSkill]:
        return list(self._load_procedural().values())

    def context(self, query: str = "", k: int = 5) -> Dict[str, Any]:
        working = self.working_recent(k)
        episodic = self.episodic_replay()[-k:]
        semantic = self.semantic_search(query)[:k] if query else self.semantic_all()[-k:] if k else []
        procedural = self.procedural_list()[:k]
        return {"tenant_id": self.tenant_id, "agent_id": self.agent_id, "working": [w.model_dump() for w in working], "episodic_recent": [e.model_dump() for e in episodic], "semantic": [s.model_dump() for s in semantic], "procedural": [p.model_dump() for p in procedural]}

    def snapshot(self) -> Dict[str, Any]:
        return {"tenant_id": self.tenant_id, "agent_id": self.agent_id, "working": [w.model_dump() for w in self._load_working()], "episodic": [e.model_dump() for e in self.episodic_replay()], "semantic": [s.model_dump() for s in self.semantic_all()], "procedural": [p.model_dump() for p in self.procedural_list()], "counts": {"working": len(self._load_working()), "episodic": len(self.episodic_replay()), "semantic": len(self.semantic_all()), "procedural": len(self.procedural_list())}}
