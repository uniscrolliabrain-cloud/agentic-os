from __future__ import annotations
from .base import Tool
class ToolRegistry:
    def __init__(self): self._tools: dict[str, Tool] = {}
    def register(self, tool: Tool): self._tools[tool.name]=tool
    def get(self, name: str): return self._tools.get(name)
