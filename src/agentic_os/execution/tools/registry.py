from __future__ import annotations
from .base import Tool


class ToolNotFoundError(Exception):
    """Tool no encontrada en el registry."""
    pass


class ToolRegistry:
    def __init__(self): self._tools: dict[str, Tool] = {}
    def register(self, tool: Tool): self._tools[tool.name]=tool
    def get(self, name: str) -> Tool:
        tool = self._tools.get(name)
        if tool is None:
            raise ToolNotFoundError(f"Tool '{name}' no encontrada en el registry")
        return tool
    def get_optional(self, name: str) -> Tool | None:
        """Devuelve la tool o None si no existe (no lanza excepción)."""
        return self._tools.get(name)
    @property
    def tools(self): return self._tools
