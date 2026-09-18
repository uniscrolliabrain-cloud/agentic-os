"""Bloque 0: Model Router (BUILD_PLAN)."""
from __future__ import annotations

import pytest

from agentic_os.interfaces.llm.router import (
    MockAdapter,
    ModelRequest,
    ModelResponse,
    ModelRouter,
)


def test_mock_adapter_responde():
    r = ModelRouter(adapters=[MockAdapter("hola")])
    resp = r.generate(ModelRequest(prompt="x"))
    assert resp.text == "hola"
    assert resp.provider == "mock"
    assert resp.fallback_used is False
    assert resp.cache_hit is False


def test_cache_hit_segunda_llamada():
    r = ModelRouter(adapters=[MockAdapter("hola")])
    r.generate(ModelRequest(prompt="x"))
    resp2 = r.generate(ModelRequest(prompt="x"))
    assert resp2.cache_hit is True


def test_cache_miss_si_prompt_distinto():
    r = ModelRouter(adapters=[MockAdapter("hola")])
    r.generate(ModelRequest(prompt="x"))
    resp2 = r.generate(ModelRequest(prompt="y"))
    assert resp2.cache_hit is False


def test_fallback_a_segundo_proveedor():
    r = ModelRouter(adapters=[MockAdapter("hola", fail=True), MockAdapter("mundo")])
    resp = r.generate(ModelRequest(prompt="x"))
    assert resp.text == "mundo"
    assert resp.fallback_used is True


def test_sin_disponibles_falla():
    r = ModelRouter(adapters=[MockAdapter("x", fail=True)])
    with pytest.raises(RuntimeError, match="fallaron"):
        r.generate(ModelRequest(prompt="x"))


def test_router_vacio_falla():
    r = ModelRouter(adapters=[])
    with pytest.raises(RuntimeError, match="ningun proveedor"):
        r.generate(ModelRequest(prompt="x"))


def test_register_anade_al_final():
    r = ModelRouter(adapters=[])
    r.register(MockAdapter("a"))
    r.register(MockAdapter("b"))
    assert len(r.available()) == 2


def test_cost_hint_cheap_prioriza_cheap():
    cheap = MockAdapter("cheap")
    cheap.name = "cheap_provider"
    cheap.cost_class = "cheap"
    exp = MockAdapter("exp")
    exp.name = "exp_provider"
    exp.cost_class = "expensive"
    r = ModelRouter(adapters=[exp, cheap])
    resp = r.generate(ModelRequest(prompt="x", cost_hint="cheap"))
    assert resp.text == "cheap"


def test_preferred_model_prioriza():
    a = MockAdapter("a")
    a.name = "a_provider"
    b = MockAdapter("b")
    b.name = "b_provider"
    b.default_model = "special-model"
    r = ModelRouter(adapters=[a, b])
    resp = r.generate(ModelRequest(prompt="x", preferred_model="special-model"))
    assert resp.text == "b"


def test_model_request_frozen():
    from pydantic import ValidationError
    req = ModelRequest(prompt="x")
    with pytest.raises(ValidationError):
        req.prompt = "y"

