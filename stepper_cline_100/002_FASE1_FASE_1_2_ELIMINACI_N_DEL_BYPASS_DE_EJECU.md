# 002/100 - FASE 1.2 — ELIMINACIÓN DEL BYPASS DE EJECUCIÓN
FASE 1 - SANITIZACIÓN Y CIMENTACIÓN DEL KERNEL
Estado: - [ ] PENDIENTE

PROTOCOLO CLINE:
1. Inspecciona repo real antes de tocar codigo
2. No copies codigo de spec ciegamente
3. NUNCA pass/TODO/.../Any/type:ignore/except:pass/bypass
4. UserContext->Policy->Command->Executor->ConnectorRouter->Connector
5. LLM!=Executor
6. Todo cambio con tests + STATUS/ARCHIVOS/CAMBIOS/TESTS/RESULTADO/INVARIANTES/RIESGOS


## PROMPT PARA CLINE
```text
# TAREA 002/100 - FASE 1.2 — ELIMINACIÓN DEL BYPASS DE EJECUCIÓN

## PROTOCOLO OBLIGATORIO ANTES DE CODIFICAR
1. Lee el estado REAL del repo: inspecciona src/, tests/, imports actuales.
2. No copies código de la especificación ciegamente. Si ya existe implementación superior, consérvala y adapta.
3. Localiza tests relacionados antes de tocar código.
4. No introduzcas pass, TODO, ..., Any, type: ignore, except: pass ni bypasses.

## CONTEXTO ARQUITECTÓNICO
Fase 1: SANITIZACIÓN Y CIMENTACIÓN DEL KERNEL
Invariante clave: LLM != Executor, Agent != Connector, Text != Command, Command != Permission. Todo efecto externo pasa por UserContext -> Policy -> Command -> Executor -> ConnectorRouter -> Connector.

## TU TAREA ESPECÍFICA
FASE 1.2 — ELIMINACIÓN DEL BYPASS DE EJECUCIÓN

Implementa exclusivamente la eliminación del bypass _PipelineExecutorHost o cualquier mecanismo equivalente descubierto en la auditoría anterior.

Archivo prioritario:

src/agentic_os/orchestration/orchestrator.py

Objetivo:

handle_pipeline() debe utilizar obligatoriamente el PipelineRunner real y debe recibir/invocar el Executor real mediante inyección explícita.

No debe existir ningún camino alternativo que permita ejecutar una herramienta o conector directamente desde el orquestador.

Regla absoluta:

ningún efecto secundario puede ejecutarse mediante tool.run(), connector.execute() directo o cualquier llamada paralela al Executor.

Todo efecto externo debe pasar por:

Command → validación → policy/kernel → ConnectorRouter/Executor → connector físico.

Conserva las APIs públicas existentes cuando sea posible.

Añade o modifica tests que demuestren que:

- el orquestador no ejecuta herramientas directamente;
- PipelineRunner recibe el Executor;
- una ejecución pasa por el Executor.

Ejecuta pytest sobre los tests relevantes.

No continúes con otras tareas.

## ENTREGABLES OBLIGATORIOS AL FINALIZAR
Debes responder con:
STATUS: PASS/FAIL
ARCHIVOS MODIFICADOS: lista
CAMBIOS: bullet points
TESTS: qué tests ejecutaste y resultado
RESULTADO: resumen técnico
INVARIANTES PROTEGIDAS: cuáles
RIESGOS: si quedan

## COMANDOS A EJECUTAR
pytest tests/ -k <relevante> -q
ruff check src tests
mypy src --ignore-missing-imports (si aplica)

No avances al siguiente prompt hasta validar este.

```

## SPEC ORIGINAL
```text
FASE 1.2 — ELIMINACIÓN DEL BYPASS DE EJECUCIÓN

Implementa exclusivamente la eliminación del bypass _PipelineExecutorHost o cualquier mecanismo equivalente descubierto en la auditoría anterior.

Archivo prioritario:

src/agentic_os/orchestration/orchestrator.py

Objetivo:

handle_pipeline() debe utilizar obligatoriamente el PipelineRunner real y debe recibir/invocar el Executor real mediante inyección explícita.

No debe existir ningún camino alternativo que permita ejecutar una herramienta o conector directamente desde el orquestador.

Regla absoluta:

ningún efecto secundario puede ejecutarse mediante tool.run(), connector.execute() directo o cualquier llamada paralela al Executor.

Todo efecto externo debe pasar por:

Command → validación → policy/kernel → ConnectorRouter/Executor → connector físico.

Conserva las APIs públicas existentes cuando sea posible.

Añade o modifica tests que demuestren que:

- el orquestador no ejecuta herramientas directamente;
- PipelineRunner recibe el Executor;
- una ejecución pasa por el Executor.

Ejecuta pytest sobre los tests relevantes.

No continúes con otras tareas.
```

## CHECKLIST
- [ ] Inspeccione repo
- [ ] No copie ciego
- [ ] Tests verdes
- [ ] Entregue STATUS etc
