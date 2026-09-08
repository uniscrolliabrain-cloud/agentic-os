# 076/100 - FASE 8.6 — SLIDING WINDOW CORRECTA
FASE 8 - EVENT SOURCING, AUDITORÍA Y RATE LIMITING
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
# TAREA 076/100 - FASE 8.6 — SLIDING WINDOW CORRECTA

## PROTOCOLO OBLIGATORIO ANTES DE CODIFICAR
1. Lee el estado REAL del repo: inspecciona src/, tests/, imports actuales.
2. No copies código de la especificación ciegamente. Si ya existe implementación superior, consérvala y adapta.
3. Localiza tests relacionados antes de tocar código.
4. No introduzcas pass, TODO, ..., Any, type: ignore, except: pass ni bypasses.

## CONTEXTO ARQUITECTÓNICO
Fase 8: EVENT SOURCING, AUDITORÍA Y RATE LIMITING
Invariante clave: LLM != Executor, Agent != Connector, Text != Command, Command != Permission. Todo efecto externo pasa por UserContext -> Policy -> Command -> Executor -> ConnectorRouter -> Connector.

## TU TAREA ESPECÍFICA
FASE 8.6 — SLIDING WINDOW CORRECTA

Audita rate_limiter.py.

Comprueba el bug descrito en la especificación:

el cálculo del cutoff de un segundo no debe compararse contra la métrica de minuto.

Implementa:

1-second window
1-minute window

de forma independiente.

Usa deque correctamente.

Corrige cualquier comparación errónea como:

queue < cutoff

cuando debería evaluarse el primer timestamp de la cola.

Añade tests temporales precisos.

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
FASE 8.6 — SLIDING WINDOW CORRECTA

Audita rate_limiter.py.

Comprueba el bug descrito en la especificación:

el cálculo del cutoff de un segundo no debe compararse contra la métrica de minuto.

Implementa:

1-second window
1-minute window

de forma independiente.

Usa deque correctamente.

Corrige cualquier comparación errónea como:

queue < cutoff

cuando debería evaluarse el primer timestamp de la cola.

Añade tests temporales precisos.
```

## CHECKLIST
- [ ] Inspeccione repo
- [ ] No copie ciego
- [ ] Tests verdes
- [ ] Entregue STATUS etc
