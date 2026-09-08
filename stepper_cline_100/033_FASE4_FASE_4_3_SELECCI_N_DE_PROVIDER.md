# 033/100 - FASE 4.3 — SELECCIÓN DE PROVIDER
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
# TAREA 033/100 - FASE 4.3 — SELECCIÓN DE PROVIDER

## PROTOCOLO OBLIGATORIO ANTES DE CODIFICAR
1. Lee el estado REAL del repo: inspecciona src/, tests/, imports actuales.
2. No copies código de la especificación ciegamente. Si ya existe implementación superior, consérvala y adapta.
3. Localiza tests relacionados antes de tocar código.
4. No introduzcas pass, TODO, ..., Any, type: ignore, except: pass ni bypasses.

## CONTEXTO ARQUITECTÓNICO
Fase 4: MODEL MESH
Invariante clave: LLM != Executor, Agent != Connector, Text != Command, Command != Permission. Todo efecto externo pasa por UserContext -> Policy -> Command -> Executor -> ConnectorRouter -> Connector.

## TU TAREA ESPECÍFICA
FASE 4.3 — SELECCIÓN DE PROVIDER

Implementa selección determinista basada en task_type y disponibilidad.

Debe existir fallback controlado.

No uses aleatoriedad.

El orden de fallback debe estar definido y probado.

Si ningún provider está disponible:

- error explícito;
- nunca respuesta inventada;
- Mock solo cuando el entorno/test lo permita explícitamente.

Añade tests para todas las combinaciones.

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
FASE 4.3 — SELECCIÓN DE PROVIDER

Implementa selección determinista basada en task_type y disponibilidad.

Debe existir fallback controlado.

No uses aleatoriedad.

El orden de fallback debe estar definido y probado.

Si ningún provider está disponible:

- error explícito;
- nunca respuesta inventada;
- Mock solo cuando el entorno/test lo permita explícitamente.

Añade tests para todas las combinaciones.
```

## CHECKLIST
- [ ] Inspeccione repo
- [ ] No copie ciego
- [ ] Tests verdes
- [ ] Entregue STATUS etc
