# 054/100 - FASE 6.4 — OAUTH MANAGER
FASE 6 - CREDENCIALES Y OAUTH
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
# TAREA 054/100 - FASE 6.4 — OAUTH MANAGER

## PROTOCOLO OBLIGATORIO ANTES DE CODIFICAR
1. Lee el estado REAL del repo: inspecciona src/, tests/, imports actuales.
2. No copies código de la especificación ciegamente. Si ya existe implementación superior, consérvala y adapta.
3. Localiza tests relacionados antes de tocar código.
4. No introduzcas pass, TODO, ..., Any, type: ignore, except: pass ni bypasses.

## CONTEXTO ARQUITECTÓNICO
Fase 6: CREDENCIALES Y OAUTH
Invariante clave: LLM != Executor, Agent != Connector, Text != Command, Command != Permission. Todo efecto externo pasa por UserContext -> Policy -> Command -> Executor -> ConnectorRouter -> Connector.

## TU TAREA ESPECÍFICA
FASE 6.4 — OAUTH MANAGER

Consolida OAuthManager.

Debe soportar:

- authorization_url;
- exchange_code;
- refresh;
- revoke.

La authorization URL debe incorporar state anti-CSRF.

No construyas query strings manualmente si la librería HTTP proporciona encoding seguro.

Los errores OAuth deben producir excepciones/resultados controlados sin revelar client_secret ni tokens.

Añade tests con HTTP mocks.

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
FASE 6.4 — OAUTH MANAGER

Consolida OAuthManager.

Debe soportar:

- authorization_url;
- exchange_code;
- refresh;
- revoke.

La authorization URL debe incorporar state anti-CSRF.

No construyas query strings manualmente si la librería HTTP proporciona encoding seguro.

Los errores OAuth deben producir excepciones/resultados controlados sin revelar client_secret ni tokens.

Añade tests con HTTP mocks.
```

## CHECKLIST
- [ ] Inspeccione repo
- [ ] No copie ciego
- [ ] Tests verdes
- [ ] Entregue STATUS etc
