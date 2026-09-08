# 016/100 - FASE 2.6 — ENTITY CLASS REGISTRY
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
# TAREA 016/100 - FASE 2.6 — ENTITY CLASS REGISTRY

## PROTOCOLO OBLIGATORIO ANTES DE CODIFICAR
1. Lee el estado REAL del repo: inspecciona src/, tests/, imports actuales.
2. No copies código de la especificación ciegamente. Si ya existe implementación superior, consérvala y adapta.
3. Localiza tests relacionados antes de tocar código.
4. No introduzcas pass, TODO, ..., Any, type: ignore, except: pass ni bypasses.

## CONTEXTO ARQUITECTÓNICO
Fase 2: ONTOLOGÍA TIPADA Y WORLDSTATE
Invariante clave: LLM != Executor, Agent != Connector, Text != Command, Command != Permission. Todo efecto externo pasa por UserContext -> Policy -> Command -> Executor -> ConnectorRouter -> Connector.

## TU TAREA ESPECÍFICA
FASE 2.6 — ENTITY CLASS REGISTRY

Crea o consolida un registro canónico equivalente a:

ENTITY_CLASS_MAP

Debe mapear cada kind a exactamente una clase física.

No permitas:

- kind desconocido;
- clase inexistente;
- dos clases para el mismo kind;
- resolución dinámica arbitraria desde input del usuario.

El registro debe ser el punto utilizado por Applier/Replay para reconstruir entidades.

Añade tests:

- cada kind conocido resuelve correctamente;
- kind desconocido produce OntologyValidationError;
- no existe fallback a BaseModel;
- no existe aceptación de tipos arbitrarios.

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
FASE 2.6 — ENTITY CLASS REGISTRY

Crea o consolida un registro canónico equivalente a:

ENTITY_CLASS_MAP

Debe mapear cada kind a exactamente una clase física.

No permitas:

- kind desconocido;
- clase inexistente;
- dos clases para el mismo kind;
- resolución dinámica arbitraria desde input del usuario.

El registro debe ser el punto utilizado por Applier/Replay para reconstruir entidades.

Añade tests:

- cada kind conocido resuelve correctamente;
- kind desconocido produce OntologyValidationError;
- no existe fallback a BaseModel;
- no existe aceptación de tipos arbitrarios.

Ejecuta pytest.
```

## CHECKLIST
- [ ] Inspeccione repo
- [ ] No copie ciego
- [ ] Tests verdes
- [ ] Entregue STATUS etc
