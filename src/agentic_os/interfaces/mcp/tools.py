from __future__ import annotations

from typing import Any, List


def expose_tools(
    registry: Any = None,
) -> List[dict]:

    if registry is None:
        return []

    tools = []

    for tool in registry.tools.values():

        tools.append(
            {
                "name": tool.name,
                "description": getattr(
                    tool,
                    "description",
                    "",
                ),
            }
        )

    return tools
