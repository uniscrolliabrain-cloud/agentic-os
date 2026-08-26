# 06 — Taxonomía de herramientas (TOOL_TAXONOMY)

Herramienta = adaptador concreto que ejecuta una operación sobre un recurso.
Cada herramienta es un `Tool` pydantic gobernado por policy. Las tool NO piensan:
ejecutan. Todo el conocimiento operativo vive en las microacciones/pipelines.

## Categorías de herramientas

### Nativas (ya en `execution/tools/`)
- `gmail_send`, `gmail_read` — correo
- `slack_send`, `slack_read` — chat colaborativo
- `whatsapp_send`, `whatsapp_read` — mensajería
- `calendar_create_event`, `calendar_list_events` — calendario
- `web_scrape`, `web_search` — web
- `documentation_create`, `documentation_search` — documentación interna

### Adapters de integración (por construir)
| Tipo | Descripción | Dónde se registra |
|---|---|---|
| `APITool` | Envuelve una API REST externa (HubSpot, Notion, Airtable, Twilio…) | `execution/tools/api_tools/` |
| `MCPTool` | Envuelve una herramienta MCP (`interfaces/mcp/`) | `execution/tools/mcp_adapter.py` |
| `FileTool` | Operaciones con ficheros locales | `execution/tools/filesystem_tool.py` |
| `DBTool` | Operaciones con bases de datos (SQL) | `execution/tools/database_tool.py` |

## Regla de integración (la ley)

El LLM **nunca** llama a una API o MCP directamente. Una integración externa se
añade SIEMPRE como `Tool` dentro del `ToolRegistry`, gobernada por `PolicyEngine`.
Flujo: `Intent → PolicyEngine → Executor → Tool(API/MCP) → EventLog`.

## Registro

Cada tool se registra en `ToolRegistry` con:
- `name` (kebab-case, único)
- `description` (para el intérprete)
- `input_schema` / `output_schema` pydantic
- `requires_approval: bool` (por defecto False; Delete/Publish → True)

Ninguna tool se puede ejecutar si su `name` no está declarado en el registry.