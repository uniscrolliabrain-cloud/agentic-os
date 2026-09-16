"""Catálogo runtime con validación fail-closed."""
from __future__ import annotations
from typing import Iterable, Optional
from .schemas import MicroActionSchema, MiniAgentSchema, PipelineSchema

class CatalogError(Exception):
    pass

class Catalog:
    def __init__(self) -> None:
        self._tools: set[str] = set()
        self._microactions: dict[str, MicroActionSchema] = {}
        self._pipelines: dict[str, PipelineSchema] = {}
        self._agents: dict[str, MiniAgentSchema] = {}

    def declare_tool(self, name: str) -> None:
        if not name or not name.strip():
            raise CatalogError("tool con nombre vacío")
        self._tools.add(name)

    def declare_tools(self, names: Iterable[str]) -> None:
        for n in names:
            self.declare_tool(n)

    def has_tool(self, name: str) -> bool:
        return name in self._tools

    def add_microaction(self, ma: MicroActionSchema) -> None:
        if ma.id in self._microactions:
            raise CatalogError(f"microacción duplicada: {ma.id}")
        if ma.tool not in self._tools:
            raise CatalogError(f"microacción '{ma.id}' referencia tool '{ma.tool}' no declarada")
        self._microactions[ma.id] = ma

    def add_pipeline(self, p: PipelineSchema) -> None:
        if p.id in self._pipelines:
            raise CatalogError(f"pipeline duplicado: {p.id}")
        for step in p.steps:
            if step.microaction_id not in self._microactions:
                raise CatalogError(f"pipeline '{p.id}' referencia microacción '{step.microaction_id}' inexistente")
        self._pipelines[p.id] = p

    def add_agent(self, a: MiniAgentSchema) -> None:
        if a.id in self._agents:
            raise CatalogError(f"agente duplicado: {a.id}")
        for ma_id in a.microactions:
            if ma_id not in self._microactions:
                raise CatalogError(f"agente '{a.id}' referencia microacción '{ma_id}' inexistente")
        for t in a.tools:
            if t not in self._tools:
                raise CatalogError(f"agente '{a.id}' referencia tool '{t}' no declarada")
        for h in a.handoffs:
            if h not in self._agents and h != a.id:
                raise CatalogError(f"agente '{a.id}' handoff a '{h}' no registrado (aún)")
        for d in a.dependencies:
            if d not in self._agents and d != a.id:
                raise CatalogError(f"agente '{a.id}' dependencia '{d}' no registrada")
        if a.sop and a.sop not in self._pipelines:
            raise CatalogError(f"agente '{a.id}' sop '{a.sop}' no es un pipeline registrado")
        self._agents[a.id] = a

    def microaction(self, ma_id: str) -> Optional[MicroActionSchema]:
        return self._microactions.get(ma_id)

    def pipeline(self, p_id: str) -> Optional[PipelineSchema]:
        return self._pipelines.get(p_id)

    def agent(self, a_id: str) -> Optional[MiniAgentSchema]:
        return self._agents.get(a_id)

    def list_microactions(self) -> list[MicroActionSchema]:
        return list(self._microactions.values())

    def list_pipelines(self) -> list[PipelineSchema]:
        return list(self._pipelines.values())

    def list_agents(self) -> list[MiniAgentSchema]:
        return list(self._agents.values())

    def __len__(self) -> int:
        return len(self._agents)

    def summary(self) -> dict:
        return {
            "tools": len(self._tools),
            "microactions": len(self._microactions),
            "pipelines": len(self._pipelines),
            "agents": len(self._agents),
        }
