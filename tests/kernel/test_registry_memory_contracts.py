"""Tests de AgentRegistry, MemoryStore y Retriever (hardening contratos)."""
from __future__ import annotations

import pytest

from agentic_os.agents.base import BaseAgent
from agentic_os.agents.registry import AgentRegistry
from agentic_os.cognition.memory.retrieval import Retriever
from agentic_os.cognition.memory.store import MemoryItem, MemoryStore


class _DummyAgent(BaseAgent):
    id = "dummy"

    def act(self, state):  # pragma: no cover - no se ejecuta
        return state


# ------------------------------------------------------------------ registry
def test_register_get_exists_remove() -> None:
    reg = AgentRegistry()
    agent = _DummyAgent()
    reg.register("a1", agent)
    assert reg.exists("a1")
    assert reg.get("a1") is agent
    assert reg.ids() == ["a1"]
    reg.remove("a1")
    assert not reg.exists("a1")
    assert len(reg) == 0


def test_register_duplicado_falla() -> None:
    reg = AgentRegistry()
    reg.register("a1", _DummyAgent())
    with pytest.raises(ValueError, match="duplicado"):
        reg.register("a1", _DummyAgent())


def test_get_agente_ausente_falla() -> None:
    reg = AgentRegistry()
    with pytest.raises(KeyError):
        reg.get("fantasma")


def test_remove_agente_ausente_falla() -> None:
    reg = AgentRegistry()
    with pytest.raises(KeyError):
        reg.remove("fantasma")


def test_register_sin_id_falla() -> None:
    with pytest.raises(ValueError):
        AgentRegistry().register("", _DummyAgent())


# --------------------------------------------------------------- memory store
def test_memory_item_inmutable() -> None:
    item = MemoryItem(id="m1", content="factura 2026", metadata={"tenant": "t1"})
    with pytest.raises(Exception):
        item.content = "otro"  # type: ignore[misc]


def test_put_get_delete() -> None:
    store = MemoryStore()
    item = MemoryItem(id="m1", content="factura")
    store.put(item)
    assert store.get("m1") is item
    store.delete("m1")
    assert store.get("m1") is None
    with pytest.raises(ValueError):
        store.put(MemoryItem(id="", content="x"))


def test_search_coincidencia_y_orden() -> None:
    store = MemoryStore()
    store.put(MemoryItem(id="m1", content="factura de compra invoice"))
    store.put(MemoryItem(id="m2", content="invoice duplicada invoice"))
    store.put(MemoryItem(id="m3", content="receta de cocina"))
    res = store.search("invoice")
    assert [i.id for i in res] == ["m2", "m1"]  # m2 tiene 2 matches
    assert len(store.search("factura")) == 1
    assert store.search("") == []
    assert store.search("nada-que-ver") == []


def test_retriever_limita_a_k() -> None:
    store = MemoryStore()
    for i in range(5):
        store.put(MemoryItem(id=f"m{i}", content=f"documento invoice {i}"))
    retriever = Retriever(store)
    assert len(retriever.retrieve("invoice", k=2)) <= 2
    assert len(retriever.retrieve("invoice", k=2)) == 2
    assert retriever.retrieve("invoice", k=0) == []
    # sin coincidencias → vacío, pero con contenido sí devuelve
    assert retriever.retrieve("cocina") == []
