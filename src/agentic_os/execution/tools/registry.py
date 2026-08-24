from __future__ import annotations
from typing import Dict, List, Optional
from .base import Tool


class ToolRegistry:
    """Registry for managing and looking up execution tools by name or capability."""

    def __init__(self) -> None:
        self._tools_by_name: Dict[str, Tool] = {}
        self._tools_by_capability: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools_by_name[tool.name] = tool
        if hasattr(tool, "capability") and tool.capability:
            self._tools_by_capability[tool.capability] = tool

    def register_all(self, tools: List[Tool]) -> None:
        for tool in tools:
            self.register(tool)

    def get(self, name_or_capability: str) -> Optional[Tool]:
        """Looks up a tool by its capability identifier first, then by name."""
        return self._tools_by_capability.get(name_or_capability) or self._tools_by_name.get(name_or_capability)

    def list_tools(self) -> List[Tool]:
        return list(self._tools_by_name.values())

