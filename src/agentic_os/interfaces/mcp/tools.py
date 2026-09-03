from __future__ import annotations

from typing import Any, List

from pydantic import BaseModel, ConfigDict, Field


class MCPTool(BaseModel):
    """Contrato Pydantic v2 de una tool expuesta vía MCP (FASE hardening).

    input_schema es un JSON Schema (mínimo {"type": "object"}); una tool sin
    schema declarado se expone con el objeto vacío genérico, nunca con Any.
    """

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    name: str = Field(min_length=1)
    description: str = ""
    input_schema: dict[str, Any] = Field(
        default_factory=lambda: {"type": "object"},
        alias="inputSchema",
    )


def expose_tools(
    registry: Any = None,
) -> List[dict]:
    """Expone las tools del ToolRegistry como contratos MCP validados.

    Cada entrada pasa por MCPTool (Pydantic): name vacío o schema no-dict
    fallan en vez de exponer contratos rotos. Determinista: el orden es el
    del registro.
    """
    if registry is None:
        return []

    tools: List[dict] = []

    for tool in registry.tools.values():

        schema = getattr(tool, "input_schema", None)
        if schema is None:
            schema = {"type": "object"}
        if not isinstance(schema, dict):
            raise TypeError(
                f"tool {tool.name!r}: input_schema debe ser dict, "
                f"recibido {type(schema).__name__}"
            )

        # Validación Pydantic: falla si name está vacío o el schema no es objeto.
        mcp_tool = MCPTool(
            name=tool.name,
            description=getattr(tool, "description", ""),
            input_schema=schema,
        )
        tools.append(mcp_tool.model_dump(by_alias=True))

    return tools

