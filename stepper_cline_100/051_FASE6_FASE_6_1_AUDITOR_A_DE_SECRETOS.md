# 051/100 - FASE 6.1 — AUDITORÍA DE SECRETOS
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
# TAREA 051/100 - FASE 6.1 — AUDITORÍA DE SECRETOS

## PROTOCOLO OBLIGATORIO ANTES DE CODIFICAR
1. Lee el estado REAL del repo: inspecciona src/, tests/, imports actuales.
2. No copies código de la especificación ciegamente. Si ya existe implementación superior, consérvala y adapta.
3. Localiza tests relacionados antes de tocar código.
4. No introduzcas pass, TODO, ..., Any, type: ignore, except: pass ni bypasses.

## CONTEXTO ARQUITECTÓNICO
Fase 6: CREDENCIALES Y OAUTH
Invariante clave: LLM != Executor, Agent != Connector, Text != Command, Command != Permission. Todo efecto externo pasa por UserContext -> Policy -> Command -> Executor -> ConnectorRouter -> Connector.

## TU TAREA ESPECÍFICA
FASE 6.1 — AUDITORÍA DE SECRETOS

Localiza todos los lugares donde se almacenan:

- API keys;
- access tokens;
- refresh tokens;
- client secrets;
- OAuth credentials.

Busca específicamente Base64 utilizado como "encryption".

No modifiques aún.

Identifica:

- almacenamiento plano;
- logs de secretos;
- secrets en EventLog;
- secrets en exceptions;
- secrets en tests;
- secrets en Git.

Entrega inventario.

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
FASE 6.1 — AUDITORÍA DE SECRETOS

Localiza todos los lugares donde se almacenan:

- API keys;
- access tokens;
- refresh tokens;
- client secrets;
- OAuth credentials.

Busca específicamente Base64 utilizado como "encryption".

No modifiques aún.

Identifica:

- almacenamiento plano;
- logs de secretos;
- secrets en EventLog;
- secrets en exceptions;
- secrets en tests;
- secrets en Git.

Entrega inventario.
```

## CHECKLIST
- [ ] Inspeccione repo
- [ ] No copie ciego
- [ ] Tests verdes
- [ ] Entregue STATUS etc
