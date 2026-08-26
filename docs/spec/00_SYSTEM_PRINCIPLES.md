# 00 — Principios del sistema

> Reglas invariables. Nada de este manual puede contradecir este archivo.

## La ley (Pydantic como sistema de tipos del mundo digital)

1. **Kernel = invariantes.** `kernel/` contiene el metamodelo (ontology, policy, world). Todo lo demás es extensión.
2. **LLM propone, el sistema dispone.** El LLM jamás ejecuta: genera un `Intent` estructurado; la policy decide; el executor ejecuta; todo se registra en el EventLog.
3. **Pydantic no es solo validación: es el sistema de tipos del mundo digital.** Cada entidad, acción, estado, contrato, microacción, pipeline y agente es un `BaseModel` (frozen). Nada entra ni sale sin cumplir su schema.

## Regla de oro

> **Un miniagente no debe "pensar cómo hacer una tarea" desde cero si ya existe un procedimiento conocido. Debe ejecutar un procedimiento estructurado y usar razonamiento solamente donde el procedimiento requiere decisión.**

## Prohibiciones absolutas

- **NO INVENTES AGENTES.** Solo se implementan los definidos en `10_AGENT_CATALOG.md`.
- **NO INVENTES ACCIONES.** Toda acción ejecutable pertenece a una categoría taxonómica de `02_TAXONOMY.md` y a un tipo de `04_ACTION_TYPES.md`.
- **NO permitas inputs arbitrarios.** Cada operación tiene un Input Schema (pydantic).
- **NO permitas outputs arbitrarios.** Cada operación tiene un Output Schema (pydantic).
- **NO permitas pipelines implícitos.** Todo pipeline se define como secuencia explícita de microacciones (`09_PIPELINE_CATALOG.md`).
- **NO rompas el núcleo.** Añadir un agente nuevo no puede modificar `kernel/`.

## La unidad mínima

La unidad más pequeña del sistema es la **microacción**: una operación atómica con contrato cerrado (ontología, input, precondiciones, SOP/tool, output, validación, errores, handoff). Las microacciones componen **pipelines**; los pipelines componen **miniagentes**; los miniagentes los compone el **orquestador**; el orquestador recibe **misiones**.

```
MICROACTIONS → PIPELINES → MINIAGENTS → ORCHESTRATOR → MISSION
```

## Jerarquía de ficheros del manual

- `00_SYSTEM_PRINCIPLES.md` — este archivo (reglas invariables)
- `01_ONTOLOGY.md` — metamodelo ENTITY / ACTION / CONTEXT / STATE
- `02_TAXONOMY.md` — 15 familias de capacidades digitales
- `03_ENTITY_TYPES.md` — catálogo de tipos de entidad
- `04_ACTION_TYPES.md` — catálogo de acciones
- `05_STATE_MACHINE.md` — máquina de estados
- `06_TOOL_TAXONOMY.md` — catálogo de herramientas y adapters
- `07_PYDANTIC_CONTRACTS.md` — schemas pydantic del sistema nervioso
- `08_MICROACTION_CATALOG.md` — catálogo de microacciones (el corazón)
- `09_PIPELINE_CATALOG.md` — pipelines explícitos
- `10_AGENT_CATALOG.md` — catálogo de miniagentes cerrados
- `11_ORCHESTRATION.md` — intérprete + router + TaskGraph/DAG
- `12_ERROR_HANDLING.md` — errores, retry, timeouts
- `13_PERMISSIONS.md` — roles/tenants → policy → capability
- `14_HUMAN_APPROVAL.md` — gate de aprobación humana
- `15_MEMORY_AND_STATE.md` — estado y memoria por misión
- `16_VALIDATION.md` — QA de cada salida contra su schema
- `17_OBSERVABILITY.md` — trazabilidad en el EventLog
- `18_TESTING.md` — criterios: un agente nuevo no rompe el núcleo
- `19_AGENT_COMPOSITION.md` — handoffs y composición
- `20_CLINE_IMPLEMENTATION_PROTOCOL.md` — cómo implementarlo