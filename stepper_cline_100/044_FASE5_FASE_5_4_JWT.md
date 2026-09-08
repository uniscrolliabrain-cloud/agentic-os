# 044/100 - FASE 5.4 — JWT
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
# TAREA 044/100 - FASE 5.4 — JWT

## PROTOCOLO OBLIGATORIO ANTES DE CODIFICAR
1. Lee el estado REAL del repo: inspecciona src/, tests/, imports actuales.
2. No copies código de la especificación ciegamente. Si ya existe implementación superior, consérvala y adapta.
3. Localiza tests relacionados antes de tocar código.
4. No introduzcas pass, TODO, ..., Any, type: ignore, except: pass ni bypasses.

## CONTEXTO ARQUITECTÓNICO
Fase 5: IDENTIDAD, MULTI-TENANCY Y POLICY ENGINE
Invariante clave: LLM != Executor, Agent != Connector, Text != Command, Command != Permission. Todo efecto externo pasa por UserContext -> Policy -> Command -> Executor -> ConnectorRouter -> Connector.

## TU TAREA ESPECÍFICA
FASE 5.4 — JWT

Consolida identity/jwt.py.

Debe existir emisión y validación de JWT firmados.

Incluye claims necesarios para:

- sub;
- tenant_id;
- roles;
- expiración;
- tipo de token cuando corresponda.

Los access tokens deben tener vida corta.

Los refresh tokens deben diferenciarse de access tokens.

No aceptes tokens expirados.

No aceptes algoritmos inseguros ni tokens sin firma.

Añade tests de:

válido;
expirado;
alterado;
tenant alterado;
roles alterados;
tipo incorrecto.

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
FASE 5.4 — JWT

Consolida identity/jwt.py.

Debe existir emisión y validación de JWT firmados.

Incluye claims necesarios para:

- sub;
- tenant_id;
- roles;
- expiración;
- tipo de token cuando corresponda.

Los access tokens deben tener vida corta.

Los refresh tokens deben diferenciarse de access tokens.

No aceptes tokens expirados.

No aceptes algoritmos inseguros ni tokens sin firma.

Añade tests de:

válido;
expirado;
alterado;
tenant alterado;
roles alterados;
tipo incorrecto.
```

## CHECKLIST
- [ ] Inspeccione repo
- [ ] No copie ciego
- [ ] Tests verdes
- [ ] Entregue STATUS etc
