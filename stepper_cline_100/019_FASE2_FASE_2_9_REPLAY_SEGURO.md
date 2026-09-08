# 019/100 - FASE 2.9 — REPLAY SEGURO
FASE 2 - ONTOLOGÍA TIPADA Y WORLDSTATE
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
# TAREA 019/100 - FASE 2.9 — REPLAY SEGURO

## PROTOCOLO OBLIGATORIO ANTES DE CODIFICAR
1. Lee el estado REAL del repo: inspecciona src/, tests/, imports actuales.
2. No copies código de la especificación ciegamente. Si ya existe implementación superior, consérvala y adapta.
3. Localiza tests relacionados antes de tocar código.
4. No introduzcas pass, TODO, ..., Any, type: ignore, except: pass ni bypasses.

## CONTEXTO ARQUITECTÓNICO
Fase 2: ONTOLOGÍA TIPADA Y WORLDSTATE
Invariante clave: LLM != Executor, Agent != Connector, Text != Command, Command != Permission. Todo efecto externo pasa por UserContext -> Policy -> Command -> Executor -> ConnectorRouter -> Connector.

## TU TAREA ESPECÍFICA
FASE 2.9 — REPLAY SEGURO

Inspecciona replay.py y validator.py.

El replay del EventLog debe reconstruir WorldState usando exactamente los mismos contratos físicos que el runtime.

Si un evento histórico contiene:

- campo desconocido;
- tipo incorrecto;
- kind inexistente;
- entidad huérfana;
- actualización de entidad inexistente;

debe fallar de manera explícita con la excepción contractual correspondiente.

NO ignores eventos corruptos silenciosamente.

Crea tests que introduzcan eventos corruptos y demuestren que replay no construye un estado aparentemente válido.

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
FASE 2.9 — REPLAY SEGURO

Inspecciona replay.py y validator.py.

El replay del EventLog debe reconstruir WorldState usando exactamente los mismos contratos físicos que el runtime.

Si un evento histórico contiene:

- campo desconocido;
- tipo incorrecto;
- kind inexistente;
- entidad huérfana;
- actualización de entidad inexistente;

debe fallar de manera explícita con la excepción contractual correspondiente.

NO ignores eventos corruptos silenciosamente.

Crea tests que introduzcan eventos corruptos y demuestren que replay no construye un estado aparentemente válido.

Ejecuta pytest.
```

## CHECKLIST
- [ ] Inspeccione repo
- [ ] No copie ciego
- [ ] Tests verdes
- [ ] Entregue STATUS etc
