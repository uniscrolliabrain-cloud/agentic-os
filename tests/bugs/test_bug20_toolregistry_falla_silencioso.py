"""Bug 20 - ToolRegistry falla silencioso + Settings duplicado: loader devuelve None y settings.py alias Groq duplicados"""

import pytest
from agentic_os.execution.tools.registry import ToolRegistry
from agentic_os.execution.tools.base import Tool


class DummyTool(Tool):
    name = "dummy_tool"
    def run(self, params: dict) -> dict:
        return {"ok": True}


def test_toolregistry_get_returns_none_for_missing():
    """ToolRegistry.get_optional() debe devolver None para tools no registrados."""
    registry = ToolRegistry()
    result = registry.get_optional("nonexistent_tool")
    assert result is None, "get_optional() debe devolver None para tools inexistentes"


def test_toolregistry_get_raises_for_missing():
    """ToolRegistry.get() debe lanzar ToolNotFoundError para tools no registrados."""
    registry = ToolRegistry()
    with pytest.raises(Exception):  # ToolNotFoundError
        registry.get("nonexistent_tool")


def test_toolregistry_get_returns_tool_when_registered():
    """ToolRegistry.get() debe devolver la tool cuando está registrada."""
    registry = ToolRegistry()
    tool = DummyTool()
    registry.register(tool)
    result = registry.get("dummy_tool")
    assert result is not None, "get() no devuelve la tool registrada"
    assert result is tool, "get() devuelve una instancia distinta"


def test_toolregistry_no_duplicate_names():
    """ToolRegistry no debe permitir registrar dos tools con el mismo nombre."""
    registry = ToolRegistry()
    tool1 = DummyTool()
    tool2 = DummyTool()
    registry.register(tool1)
    registry.register(tool2)  # Debe sobrescribir o rechazar
    # El comportamiento esperado: la última registration gana
    assert registry.get("dummy_tool") is tool2


def test_settings_no_duplicate_groq_alias():
    """Settings no debe tener alias duplicados para GROQ_API_KEY."""
    import inspect
    from agentic_os.infrastructure.config import settings
    source = inspect.getsource(settings)

    # Contar cuántas veces aparece GROQ_API_KEY en Field definitions
    count = source.count("GROQ_API_KEY")
    assert count <= 2, f"GROQ_API_KEY aparece {count} veces en settings.py (duplicado)"


def test_settings_groq_fields_consistent():
    """Los campos de Groq en Settings deben ser consistentes."""
    from agentic_os.infrastructure.config.settings import Settings
    s = Settings()
    # Si tiene groq_api_key, debe poder accederse sin error
    assert hasattr(s, "groq_api_key"), "Settings no tiene groq_api_key"
    assert hasattr(s, "groq_model"), "Settings no tiene groq_model"
