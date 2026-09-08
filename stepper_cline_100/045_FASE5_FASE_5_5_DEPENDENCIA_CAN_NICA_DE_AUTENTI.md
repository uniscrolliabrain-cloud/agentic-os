# 045/100 - FASE 5.5 — DEPENDENCIA CANÓNICA DE AUTENTICACIÓN
FASE 5 - IDENTIDAD, MULTI-TENANCY Y POLICY ENGINE
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
# TAREA 045/100 - FASE 5.5 — DEPENDENCIA CANÓNICA DE AUTENTICACIÓN

## PROTOCOLO OBLIGATORIO ANTES DE CODIFICAR
1. Lee el estado REAL del repo: inspecciona src/, tests/, imports actuales.
2. No copies código de la especificación ciegamente. Si ya existe implementación superior, consérvala y adapta.
3. Localiza tests relacionados antes de tocar código.
4. No introduzcas pass, TODO, ..., Any, type: ignore, except: pass ni bypasses.

## CONTEXTO ARQUITECTÓNICO
Fase 5: IDENTIDAD, MULTI-TENANCY Y POLICY ENGINE
Invariante clave: LLM != Executor, Agent != Connector, Text != Command, Command != Permission. Todo efecto externo pasa por UserContext -> Policy -> Command -> Executor -> ConnectorRouter -> Connector.

## TU TAREA ESPECÍFICA
FASE 5.5 — DEPENDENCIA CANÓNICA DE AUTENTICACIÓN

Consolida:

src/agentic_os/interfaces/api/deps.py

get_current_user() debe:

1. procesar Bearer JWT;
2. validar firma;
3. validar expiración;
4. recuperar usuario;
5. validar usuario activo;
6. resolver tenant;
7. construir UserContext.

Si existe API-Key legacy, mantenla solo si es necesaria y explícitamente limitada.

Corrige cualquier parsing incorrecto del header Authorization.

Nunca extraigas el token usando índices arbitrarios de split().

Añade tests API.

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
FASE 5.5 — DEPENDENCIA CANÓNICA DE AUTENTICACIÓN

Consolida:

src/agentic_os/interfaces/api/deps.py

get_current_user() debe:

1. procesar Bearer JWT;
2. validar firma;
3. validar expiración;
4. recuperar usuario;
5. validar usuario activo;
6. resolver tenant;
7. construir UserContext.

Si existe API-Key legacy, mantenla solo si es necesaria y explícitamente limitada.

Corrige cualquier parsing incorrecto del header Authorization.

Nunca extraigas el token usando índices arbitrarios de split().

Añade tests API.
```

## CHECKLIST
- [ ] Inspeccione repo
- [ ] No copie ciego
- [ ] Tests verdes
- [ ] Entregue STATUS etc
