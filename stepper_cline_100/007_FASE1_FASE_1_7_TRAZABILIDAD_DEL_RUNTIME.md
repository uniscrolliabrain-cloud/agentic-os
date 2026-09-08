# 007/100 - FASE 1.7 — TRAZABILIDAD DEL RUNTIME
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
# TAREA 007/100 - FASE 1.7 — TRAZABILIDAD DEL RUNTIME

## PROTOCOLO OBLIGATORIO ANTES DE CODIFICAR
1. Lee el estado REAL del repo: inspecciona src/, tests/, imports actuales.
2. No copies código de la especificación ciegamente. Si ya existe implementación superior, consérvala y adapta.
3. Localiza tests relacionados antes de tocar código.
4. No introduzcas pass, TODO, ..., Any, type: ignore, except: pass ni bypasses.

## CONTEXTO ARQUITECTÓNICO
Fase 1: SANITIZACIÓN Y CIMENTACIÓN DEL KERNEL
Invariante clave: LLM != Executor, Agent != Connector, Text != Command, Command != Permission. Todo efecto externo pasa por UserContext -> Policy -> Command -> Executor -> ConnectorRouter -> Connector.

## TU TAREA ESPECÍFICA
FASE 1.7 — TRAZABILIDAD DEL RUNTIME

Audita la propagación de:

- tenant_id
- correlation_id
- command_id
- actor_id

desde:

REST/API
→ Orchestrator
→ PipelineRunner
→ Executor
→ Connector
→ EventLog.

El objetivo es que ninguna operación relevante pierda su identidad de trazabilidad.

No generes identificadores nuevos innecesariamente si ya existe una abstracción canónica.

Cuando sea obligatorio generar uno, hazlo en el límite correcto de la capa.

Añade tests que comprueben que una misma ejecución conserva correlation_id y command_id a través de todas las capas.

No modifiques todavía la semántica de autenticación JWT.

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
FASE 1.7 — TRAZABILIDAD DEL RUNTIME

Audita la propagación de:

- tenant_id
- correlation_id
- command_id
- actor_id

desde:

REST/API
→ Orchestrator
→ PipelineRunner
→ Executor
→ Connector
→ EventLog.

El objetivo es que ninguna operación relevante pierda su identidad de trazabilidad.

No generes identificadores nuevos innecesariamente si ya existe una abstracción canónica.

Cuando sea obligatorio generar uno, hazlo en el límite correcto de la capa.

Añade tests que comprueben que una misma ejecución conserva correlation_id y command_id a través de todas las capas.

No modifiques todavía la semántica de autenticación JWT.
```

## CHECKLIST
- [ ] Inspeccione repo
- [ ] No copie ciego
- [ ] Tests verdes
- [ ] Entregue STATUS etc
