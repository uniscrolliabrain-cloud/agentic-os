# 006/100 - FASE 1.6 — CONTRATO ÚNICO DE PIPELINES
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
# TAREA 006/100 - FASE 1.6 — CONTRATO ÚNICO DE PIPELINES

## PROTOCOLO OBLIGATORIO ANTES DE CODIFICAR
1. Lee el estado REAL del repo: inspecciona src/, tests/, imports actuales.
2. No copies código de la especificación ciegamente. Si ya existe implementación superior, consérvala y adapta.
3. Localiza tests relacionados antes de tocar código.
4. No introduzcas pass, TODO, ..., Any, type: ignore, except: pass ni bypasses.

## CONTEXTO ARQUITECTÓNICO
Fase 1: SANITIZACIÓN Y CIMENTACIÓN DEL KERNEL
Invariante clave: LLM != Executor, Agent != Connector, Text != Command, Command != Permission. Todo efecto externo pasa por UserContext -> Policy -> Command -> Executor -> ConnectorRouter -> Connector.

## TU TAREA ESPECÍFICA
FASE 1.6 — CONTRATO ÚNICO DE PIPELINES

Inspecciona:

src/agentic_os/orchestration/pipelines/runner.py

y todas las pipelines existentes, incluyendo:

- daily_social
- inbox_watcher
- leads_to_draft

Normaliza su interfaz al contrato definido por la especificación:

run(
    runner: PipelineRunner,
    tenant_id: str,
    params: dict,
    correlation_id: str | None = None
) -> dict

No destruyas compatibilidad innecesariamente.

Si existen firmas antiguas, adapta las implementaciones y los call sites.

El PipelineRunner debe seguir siendo el punto de ejecución de la pipeline y no una fachada que permita saltarse el Executor.

Añade tests de contrato para todas las pipelines existentes.

Ejecuta pytest.

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
FASE 1.6 — CONTRATO ÚNICO DE PIPELINES

Inspecciona:

src/agentic_os/orchestration/pipelines/runner.py

y todas las pipelines existentes, incluyendo:

- daily_social
- inbox_watcher
- leads_to_draft

Normaliza su interfaz al contrato definido por la especificación:

run(
    runner: PipelineRunner,
    tenant_id: str,
    params: dict,
    correlation_id: str | None = None
) -> dict

No destruyas compatibilidad innecesariamente.

Si existen firmas antiguas, adapta las implementaciones y los call sites.

El PipelineRunner debe seguir siendo el punto de ejecución de la pipeline y no una fachada que permita saltarse el Executor.

Añade tests de contrato para todas las pipelines existentes.

Ejecuta pytest.
```

## CHECKLIST
- [ ] Inspeccione repo
- [ ] No copie ciego
- [ ] Tests verdes
- [ ] Entregue STATUS etc
