# 20 — Protocolo de implementación (para Cline)

Cómo implementar este sistema en el repositorio **sin romper la ley** ni inventar nada.

## 1. Postura

> **Cline es el implementador de una arquitectura ya definida, no el arquitecto.**

Cline NO decide qué significa "trabajar digitalmente": implementa esta spec.

## 2. Prohibiciones en código

- NO inventar miniagentes: usar solo `10_AGENT_CATALOG.md`.
- NO inventar microacciones/pipelines: configurar las del catálogo.
- NO ejecutar acciones fuera de un pipeline definido.
- NO tocar `kernel/` (salvo bug explícito).
- NO dejar que el LLM ejecute nada.
- NO usar tools no declaradas en `ToolRegistry`.

## 3. Estructura de carpetas

```
src/agentic_os/
├── kernel/                 # NO tocar (invariantes)
├── cognition/
│   ├── agents/             # catálogo (schemas.py, catalog.py, runner.py)
│   ├── skills/             # skill/SOP base (ya existe)
│   └── planning/           # intent, plan, taskgraph
├── execution/
│   ├── skill_runner.py     # motor de pipelines
│   ├── tools/              # tools + api_tools/ + mcp_adapter.py
│   └── approvals.py        # gate humano (14)
├── orchestration/
│   ├── interpreter.py      # router determinista + intérprete LLM
│   └── orchestrator.py     # ya existe
├── interfaces/
│   ├── api/rest.py         # +/api/approvals, /api/missions
│   └── llm/                # Laia (PR) y providers
[] 
tests/
├── kernel/  # no tocar
├── agents/  # test por agente
└── ...
```

## 4. Orden de implementación (fases con commit+push cada una)

- **Fase 1**: `schemas.py` (07) + validador del catálogo + `SkillRunner`.
- **Fase 2**: miniagente de referencia WEB_RESEARCH_AGENT end-to-end (leader), con QA y, si publica, approval.
- **Fase 3**: miniagentes de negocio (LEAD_GENERATION, COMMUNICATION, DATA_ANALYSIS, CONTENT) construidos sobre las microacciones del catálogo.
- **Fase 4**: Adapters de APIs/MCP como tools gobernadas; más familias/microacciones.

## 5. Convenciones

- Kebab-case para ids (`web.search_web`), `snake_case` para código Python.
- Todo `BaseModel` core con `ConfigDict(frozen=True)`.
- Docstrings en español, tabla `MISSION`/`HANDOFF` donde conste cada contrato.
- Commits de una fase, con tests verdes, y push por fase.

## 6. Criterio de aceptación por fase

- `pytest` verde (incluye `tests/kernel/` intactos).
- Todos los ids del catálogo únicos y referencias resueltas.
- `Cline_implement` loguea cada ejecución al EventLog (observabilidad).
- La demo Laia → misión → EventLog funciona en localhost.

## 7. Si algo no está en la spec

- No lo inventes: ABRE una duda al usuario (o añade a `docs/spec/` tras aprobación), no un hack en código.