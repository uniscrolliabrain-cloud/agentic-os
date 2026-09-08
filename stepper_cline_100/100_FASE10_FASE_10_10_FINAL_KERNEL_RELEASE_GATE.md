# 100/100 - FASE 10.10 — FINAL KERNEL RELEASE GATE
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
# TAREA 100/100 - FASE 10.10 — FINAL KERNEL RELEASE GATE

## PROTOCOLO OBLIGATORIO ANTES DE CODIFICAR
1. Lee el estado REAL del repo: inspecciona src/, tests/, imports actuales.
2. No copies código de la especificación ciegamente. Si ya existe implementación superior, consérvala y adapta.
3. Localiza tests relacionados antes de tocar código.
4. No introduzcas pass, TODO, ..., Any, type: ignore, except: pass ni bypasses.

## CONTEXTO ARQUITECTÓNICO
Fase 10: HARDENING FINAL, TESTS Y PRODUCCIÓN
Invariante clave: LLM != Executor, Agent != Connector, Text != Command, Command != Permission. Todo efecto externo pasa por UserContext -> Policy -> Command -> Executor -> ConnectorRouter -> Connector.

## TU TAREA ESPECÍFICA
FASE 10.10 — FINAL KERNEL RELEASE GATE

Este es el último paso.

NO IMPLEMENTES NINGUNA FUNCIONALIDAD NUEVA.

Realiza una auditoría final completa del repositorio contra la especificación.

Ejecuta:

pytest tests/

ruff check src tests

mypy src

y cualquier test de integración existente.

Después realiza búsquedas finales de:

tool.run(
direct connector execution
datetime.utcnow()
datetime.now(timezone.utc)
DEV_ALLOW_ALL
dict[str, Any]
pass
TODO
hardcoded secrets
API keys
refresh tokens
Bearer tokens
wildcard allow
cross-tenant access
except Exception silencioso

Comprueba especialmente que las siguientes invariantes sean físicamente verdaderas:

INVARIANTE 1
Ningún LLM ejecuta efectos externos.

INVARIANTE 2
Ningún agente ejecuta connectors directamente.

INVARIANTE 3
Todo efecto externo pasa por Command → Policy/Kernel → Executor → Connector.

INVARIANTE 4
Los datos contractuales críticos están tipados con Pydantic.

INVARIANTE 5
WorldState no acepta entidades arbitrarias.

INVARIANTE 6
Replay no acepta eventos corruptos silenciosamente.

INVARIANTE 7
Tenant A no puede acceder a Tenant B.

INVARIANTE 8
Default-Deny permanece activo en producción.

INVARIANTE 9
delete/publish respetan human approval.

INVARIANTE 10
Los secretos no aparecen en código, logs ni EventLog.

INVARIANTE 11
Si la auditoría obligatoria falla, la operación no se declara exitosa.

INVARIANTE 12
El SMC clasifica/cristaliza pero NO ejecuta.

INVARIANTE 13
El ModelRouter devuelve resultados que respetan el contrato solicitado.

INVARIANTE 14
Los connectors solo ejecutan capabilities registradas.

INVARIANTE 15
Las pipelines utilizan una interfaz coherente.

INVARIANTE 16
Los límites de Agent/Skill/Pipeline se aplican realmente.

INVARIANTE 17
RateLimiter respeta segundo y minuto independientemente.

INVARIANTE 18
JWT no puede falsificarse ni cambiar tenant/roles.

INVARIANTE 19
OAuth credentials se almacenan cifradas.

INVARIANTE 20
No existen bypasses ocultos alrededor del Kernel.

ENTREGA FINAL:

1. Estado de tests.
2. Estado de ruff.
3. Estado de mypy.
4. Archivos modificados.
5. Invariantes PASS.
6. Invariantes FAIL.
7. Riesgos residuales.
8. Deuda técnica residual.
9. Recomendación RELEASE: YES/NO.

NO declares RELEASE YES si existe una violación crítica de seguridad, tenant isolation, ejecución, persistencia o contrato Pydantic.

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
FASE 10.10 — FINAL KERNEL RELEASE GATE

Este es el último paso.

NO IMPLEMENTES NINGUNA FUNCIONALIDAD NUEVA.

Realiza una auditoría final completa del repositorio contra la especificación.

Ejecuta:

pytest tests/

ruff check src tests

mypy src

y cualquier test de integración existente.

Después realiza búsquedas finales de:

tool.run(
direct connector execution
datetime.utcnow()
datetime.now(timezone.utc)
DEV_ALLOW_ALL
dict[str, Any]
pass
TODO
hardcoded secrets
API keys
refresh tokens
Bearer tokens
wildcard allow
cross-tenant access
except Exception silencioso

Comprueba especialmente que las siguientes invariantes sean físicamente verdaderas:

INVARIANTE 1
Ningún LLM ejecuta efectos externos.

INVARIANTE 2
Ningún agente ejecuta connectors directamente.

INVARIANTE 3
Todo efecto externo pasa por Command → Policy/Kernel → Executor → Connector.

INVARIANTE 4
Los datos contractuales críticos están tipados con Pydantic.

INVARIANTE 5
WorldState no acepta entidades arbitrarias.

INVARIANTE 6
Replay no acepta eventos corruptos silenciosamente.

INVARIANTE 7
Tenant A no puede acceder a Tenant B.

INVARIANTE 8
Default-Deny permanece activo en producción.

INVARIANTE 9
delete/publish respetan human approval.

INVARIANTE 10
Los secretos no aparecen en código, logs ni EventLog.

INVARIANTE 11
Si la auditoría obligatoria falla, la operación no se declara exitosa.

INVARIANTE 12
El SMC clasifica/cristaliza pero NO ejecuta.

INVARIANTE 13
El ModelRouter devuelve resultados que respetan el contrato solicitado.

INVARIANTE 14
Los connectors solo ejecutan capabilities registradas.

INVARIANTE 15
Las pipelines utilizan una interfaz coherente.

INVARIANTE 16
Los límites de Agent/Skill/Pipeline se aplican realmente.

INVARIANTE 17
RateLimiter respeta segundo y minuto independientemente.

INVARIANTE 18
JWT no puede falsificarse ni cambiar tenant/roles.

INVARIANTE 19
OAuth credentials se almacenan cifradas.

INVARIANTE 20
No existen bypasses ocultos alrededor del Kernel.

ENTREGA FINAL:

1. Estado de tests.
2. Estado de ruff.
3. Estado de mypy.
4. Archivos modificados.
5. Invariantes PASS.
6. Invariantes FAIL.
7. Riesgos residuales.
8. Deuda técnica residual.
9. Recomendación RELEASE: YES/NO.

NO declares RELEASE YES si existe una violación crítica de seguridad, tenant isolation, ejecución, persistencia o contrato Pydantic.
```

## CHECKLIST
- [ ] Inspeccione repo
- [ ] No copie ciego
- [ ] Tests verdes
- [ ] Entregue STATUS etc
