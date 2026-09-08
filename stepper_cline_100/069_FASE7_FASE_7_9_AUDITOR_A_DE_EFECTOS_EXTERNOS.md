# 069/100 - FASE 7.9 — AUDITORÍA DE EFECTOS EXTERNOS
FASE 7 - CONECTORES REALES GOOGLE / HUBSPOT / SLACK
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
# TAREA 069/100 - FASE 7.9 — AUDITORÍA DE EFECTOS EXTERNOS

## PROTOCOLO OBLIGATORIO ANTES DE CODIFICAR
1. Lee el estado REAL del repo: inspecciona src/, tests/, imports actuales.
2. No copies código de la especificación ciegamente. Si ya existe implementación superior, consérvala y adapta.
3. Localiza tests relacionados antes de tocar código.
4. No introduzcas pass, TODO, ..., Any, type: ignore, except: pass ni bypasses.

## CONTEXTO ARQUITECTÓNICO
Fase 7: CONECTORES REALES GOOGLE / HUBSPOT / SLACK
Invariante clave: LLM != Executor, Agent != Connector, Text != Command, Command != Permission. Todo efecto externo pasa por UserContext -> Policy -> Command -> Executor -> ConnectorRouter -> Connector.

## TU TAREA ESPECÍFICA
FASE 7.9 — AUDITORÍA DE EFECTOS EXTERNOS

Cada ejecución física debe generar un registro de auditoría con:

tenant;
actor;
command;
capability;
connector;
provider;
operation;
status;
duration;
approval reference cuando corresponda.

No registrar secretos.

Si la persistencia de auditoría es obligatoria y falla:

→ fail-closed.

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
FASE 7.9 — AUDITORÍA DE EFECTOS EXTERNOS

Cada ejecución física debe generar un registro de auditoría con:

tenant;
actor;
command;
capability;
connector;
provider;
operation;
status;
duration;
approval reference cuando corresponda.

No registrar secretos.

Si la persistencia de auditoría es obligatoria y falla:

→ fail-closed.

Añade tests.
```

## CHECKLIST
- [ ] Inspeccione repo
- [ ] No copie ciego
- [ ] Tests verdes
- [ ] Entregue STATUS etc
