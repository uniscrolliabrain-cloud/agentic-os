# 018/100 - FASE 2.8 — WORLD APPLIER
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
# TAREA 018/100 - FASE 2.8 — WORLD APPLIER

## PROTOCOLO OBLIGATORIO ANTES DE CODIFICAR
1. Lee el estado REAL del repo: inspecciona src/, tests/, imports actuales.
2. No copies código de la especificación ciegamente. Si ya existe implementación superior, consérvala y adapta.
3. Localiza tests relacionados antes de tocar código.
4. No introduzcas pass, TODO, ..., Any, type: ignore, except: pass ni bypasses.

## CONTEXTO ARQUITECTÓNICO
Fase 2: ONTOLOGÍA TIPADA Y WORLDSTATE
Invariante clave: LLM != Executor, Agent != Connector, Text != Command, Command != Permission. Todo efecto externo pasa por UserContext -> Policy -> Command -> Executor -> ConnectorRouter -> Connector.

## TU TAREA ESPECÍFICA
FASE 2.8 — WORLD APPLIER

Modifica:

src/agentic_os/kernel/world/applier.py

El Applier debe:

1. recibir Event;
2. identificar event.kind;
3. resolver el tipo físico;
4. validar payload con Pydantic;
5. construir el nuevo estado;
6. NO mutar el estado original;
7. fallar con OntologyValidationError ante payload inválido.

Para entity_created:

- exigir kind;
- rechazar kind desconocido;
- rechazar campos desconocidos.

Para entity_updated:

- exigir entidad existente;
- fusionar de forma controlada;
- volver a validar el objeto completo.

Para entity_deleted:

- aplicar las reglas existentes de invariantes.

Añade tests transaccionales.

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
FASE 2.8 — WORLD APPLIER

Modifica:

src/agentic_os/kernel/world/applier.py

El Applier debe:

1. recibir Event;
2. identificar event.kind;
3. resolver el tipo físico;
4. validar payload con Pydantic;
5. construir el nuevo estado;
6. NO mutar el estado original;
7. fallar con OntologyValidationError ante payload inválido.

Para entity_created:

- exigir kind;
- rechazar kind desconocido;
- rechazar campos desconocidos.

Para entity_updated:

- exigir entidad existente;
- fusionar de forma controlada;
- volver a validar el objeto completo.

Para entity_deleted:

- aplicar las reglas existentes de invariantes.

Añade tests transaccionales.
```

## CHECKLIST
- [ ] Inspeccione repo
- [ ] No copie ciego
- [ ] Tests verdes
- [ ] Entregue STATUS etc
