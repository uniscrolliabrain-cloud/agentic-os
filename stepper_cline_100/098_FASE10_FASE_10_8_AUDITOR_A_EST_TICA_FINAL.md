# 098/100 - FASE 10.8 — AUDITORÍA ESTÁTICA FINAL
FASE 10 - HARDENING FINAL, TESTS Y PRODUCCIÓN
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
# TAREA 098/100 - FASE 10.8 — AUDITORÍA ESTÁTICA FINAL

## PROTOCOLO OBLIGATORIO ANTES DE CODIFICAR
1. Lee el estado REAL del repo: inspecciona src/, tests/, imports actuales.
2. No copies código de la especificación ciegamente. Si ya existe implementación superior, consérvala y adapta.
3. Localiza tests relacionados antes de tocar código.
4. No introduzcas pass, TODO, ..., Any, type: ignore, except: pass ni bypasses.

## CONTEXTO ARQUITECTÓNICO
Fase 10: HARDENING FINAL, TESTS Y PRODUCCIÓN
Invariante clave: LLM != Executor, Agent != Connector, Text != Command, Command != Permission. Todo efecto externo pasa por UserContext -> Policy -> Command -> Executor -> ConnectorRouter -> Connector.

## TU TAREA ESPECÍFICA
FASE 10.8 — AUDITORÍA ESTÁTICA FINAL

Ejecuta:

ruff check src tests
mypy src

y cualquier formatter/check configurado por el proyecto.

Después inspecciona manualmente errores restantes.

No uses:

# type: ignore

noqa

o exclusiones globales

para ocultar errores nuevos salvo justificación técnica explícita.

Comprueba imports circulares.

Comprueba módulos muertos.

Comprueba referencias a clases eliminadas.

Corrige todo lo atribuible a la consolidación.

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
FASE 10.8 — AUDITORÍA ESTÁTICA FINAL

Ejecuta:

ruff check src tests
mypy src

y cualquier formatter/check configurado por el proyecto.

Después inspecciona manualmente errores restantes.

No uses:

# type: ignore

noqa

o exclusiones globales

para ocultar errores nuevos salvo justificación técnica explícita.

Comprueba imports circulares.

Comprueba módulos muertos.

Comprueba referencias a clases eliminadas.

Corrige todo lo atribuible a la consolidación.
```

## CHECKLIST
- [ ] Inspeccione repo
- [ ] No copie ciego
- [ ] Tests verdes
- [ ] Entregue STATUS etc
