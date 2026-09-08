# 037/100 - FASE 4.7 — EVENTLOG DEL MODEL MESH
FASE 4 - MODEL MESH
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
# TAREA 037/100 - FASE 4.7 — EVENTLOG DEL MODEL MESH

## PROTOCOLO OBLIGATORIO ANTES DE CODIFICAR
1. Lee el estado REAL del repo: inspecciona src/, tests/, imports actuales.
2. No copies código de la especificación ciegamente. Si ya existe implementación superior, consérvala y adapta.
3. Localiza tests relacionados antes de tocar código.
4. No introduzcas pass, TODO, ..., Any, type: ignore, except: pass ni bypasses.

## CONTEXTO ARQUITECTÓNICO
Fase 4: MODEL MESH
Invariante clave: LLM != Executor, Agent != Connector, Text != Command, Command != Permission. Todo efecto externo pasa por UserContext -> Policy -> Command -> Executor -> ConnectorRouter -> Connector.

## TU TAREA ESPECÍFICA
FASE 4.7 — EVENTLOG DEL MODEL MESH

Cada decisión de routing debe producir un evento auditable cuando la arquitectura actual lo requiera.

Registra como mínimo:

- tenant_id;
- correlation_id;
- task_type;
- provider;
- success;
- latency_ms;
- error cuando exista.

No registres:

- API keys;
- tokens;
- prompts completos sensibles;
- secretos.

Si EventLog falla y la auditoría es obligatoria según el kernel, aplica fail-closed.

Añade tests.

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
FASE 4.7 — EVENTLOG DEL MODEL MESH

Cada decisión de routing debe producir un evento auditable cuando la arquitectura actual lo requiera.

Registra como mínimo:

- tenant_id;
- correlation_id;
- task_type;
- provider;
- success;
- latency_ms;
- error cuando exista.

No registres:

- API keys;
- tokens;
- prompts completos sensibles;
- secretos.

Si EventLog falla y la auditoría es obligatoria según el kernel, aplica fail-closed.

Añade tests.
```

## CHECKLIST
- [ ] Inspeccione repo
- [ ] No copie ciego
- [ ] Tests verdes
- [ ] Entregue STATUS etc
