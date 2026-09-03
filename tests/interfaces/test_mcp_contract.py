"""Tests del contrato MCP endurecido (#14 del hardening)."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from agentic_os.interfaces.mcp.server import MCPServer
from agentic_os.interfaces.mcp.tools import MCPTool, expose_tools


def test_mcp_tool_contrato_valido() -> None:
    t = MCPTool(name="gmail_send", description="envía email", input_schema={"type": "object"})
    assert t.name == "gmail_send"
    assert t.input_schema == {"type": "object"}


def test_mcp_tool_schema_default_es_objeto() -> None:
    t = MCPTool(name="x")
    assert t.input_schema == {"type": "object"}


def test_mcp_tool_name_vacio_rechazado() -> None:
    with pytest.raises(ValidationError):
        MCPTool(name="")


def test_mcp_tool_schema_no_dict_rechazado() -> None:
    with pytest.raises(ValidationError):
        MCPTool(name="x", input_schema="not-a-dict")


class _FakeRegistry:
    def __init__(self, tools):
        self.tools = {t.name: t for t in tools}


class _FakeTool:
    def __init__(self, name, description="", input_schema=None):
        self.name = name
        self.description = description
        if input_schema is not None:
            self.input_schema = input_schema


def test_expose_tools_valida_y_es_determinista() -> None:
    reg = _FakeRegistry(
        [_FakeTool("b_tool", "B"), _FakeTool("a_tool", "A")]
    )
    out = expose_tools(reg)
    assert [t["name"] for t in out] == ["b_tool", "a_tool"]  # orden del registro
    assert out[0]["inputSchema"] == {"type": "object"}  # alias por defecto


def test_expose_tools_registry_vacio() -> None:
    assert expose_tools(None) == []
    assert expose_tools(_FakeRegistry([])) == []


def test_expose_tools_schema_roto_falla() -> None:
    reg = _FakeRegistry([_FakeTool("bad", input_schema="oops")])
    with pytest.raises(TypeError):
        expose_tools(reg)


# ------------------------------------------------------------------- server
def test_server_call_requiere_start() -> None:
    s = MCPServer()
    s.register("echo", lambda p: p)
    with pytest.raises(RuntimeError):
        s.call("echo", {"x": 1})


def test_server_call_metodo_inexistente() -> None:
    s = MCPServer()
    s.start()
    with pytest.raises(KeyError):
        s.call("nope", {})


def test_server_call_valida_params_no_dict() -> None:
    s = MCPServer()
    s.start()
    s.register("echo", lambda p: p)
    with pytest.raises(TypeError):
        s.call("echo", "not-a-dict")  # type: ignore[arg-type]


def test_server_call_ok_y_registro_valida_nombre() -> None:
    s = MCPServer()
    s.start()
    s.register("echo", lambda p: p)
    assert s.call("echo", {"a": 1}) == {"a": 1}
    with pytest.raises(ValueError):
        s.register("", lambda p: p)
