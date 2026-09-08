# 010/100 - FASE 1.10 — GATE DE CIERRE
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
# TAREA 010/100 - FASE 1.10 — GATE DE CIERRE

## PROTOCOLO OBLIGATORIO ANTES DE CODIFICAR
1. Lee el estado REAL del repo: inspecciona src/, tests/, imports actuales.
2. No copies código de la especificación ciegamente. Si ya existe implementación superior, consérvala y adapta.
3. Localiza tests relacionados antes de tocar código.
4. No introduzcas pass, TODO, ..., Any, type: ignore, except: pass ni bypasses.

## CONTEXTO ARQUITECTÓNICO
Fase 1: SANITIZACIÓN Y CIMENTACIÓN DEL KERNEL
Invariante clave: LLM != Executor, Agent != Connector, Text != Command, Command != Permission. Todo efecto externo pasa por UserContext -> Policy -> Command -> Executor -> ConnectorRouter -> Connector.

## TU TAREA ESPECÍFICA
FASE 1.10 — GATE DE CIERRE

No implementes funcionalidades nuevas.

Haz una auditoría final de FASE 1.

Verifica mecánicamente:

- no existe bypass de PipelineExecutor;
- efectos externos pasan por Executor;
- PipelineRunner tiene contrato único;
- now_utc() es la abstracción temporal canónica donde corresponde;
- EventLog failure es fail-closed;
- tenant_id/correlation_id/command_id se propagan;
- tests verdes;
- ruff limpio;
- mypy limpio o con errores preexistentes explícitamente documentados.

Ejecuta:

pytest tests/
ruff check src tests
mypy src

Entrega:

FASE 1 = PASS/FAIL

y una lista de archivos modificados.

Si cualquier invariante crítica falla, NO declares PASS.

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
FASE 1.10 — GATE DE CIERRE

No implementes funcionalidades nuevas.

Haz una auditoría final de FASE 1.

Verifica mecánicamente:

- no existe bypass de PipelineExecutor;
- efectos externos pasan por Executor;
- PipelineRunner tiene contrato único;
- now_utc() es la abstracción temporal canónica donde corresponde;
- EventLog failure es fail-closed;
- tenant_id/correlation_id/command_id se propagan;
- tests verdes;
- ruff limpio;
- mypy limpio o con errores preexistentes explícitamente documentados.

Ejecuta:

pytest tests/
ruff check src tests
mypy src

Entrega:

FASE 1 = PASS/FAIL

y una lista de archivos modificados.

Si cualquier invariante crítica falla, NO declares PASS.
```

## CHECKLIST
- [ ] Inspeccione repo
- [ ] No copie ciego
- [ ] Tests verdes
- [ ] Entregue STATUS etc
