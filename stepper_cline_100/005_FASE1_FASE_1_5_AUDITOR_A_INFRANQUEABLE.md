# 005/100 - FASE 1.5 — AUDITORÍA INFRANQUEABLE
FASE 1 - SANITIZACIÓN Y CIMENTACIÓN DEL KERNEL
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
# TAREA 005/100 - FASE 1.5 — AUDITORÍA INFRANQUEABLE

## PROTOCOLO OBLIGATORIO ANTES DE CODIFICAR
1. Lee el estado REAL del repo: inspecciona src/, tests/, imports actuales.
2. No copies código de la especificación ciegamente. Si ya existe implementación superior, consérvala y adapta.
3. Localiza tests relacionados antes de tocar código.
4. No introduzcas pass, TODO, ..., Any, type: ignore, except: pass ni bypasses.

## CONTEXTO ARQUITECTÓNICO
Fase 1: SANITIZACIÓN Y CIMENTACIÓN DEL KERNEL
Invariante clave: LLM != Executor, Agent != Connector, Text != Command, Command != Permission. Todo efecto externo pasa por UserContext -> Policy -> Command -> Executor -> ConnectorRouter -> Connector.

## TU TAREA ESPECÍFICA
FASE 1.5 — AUDITORÍA INFRANQUEABLE

Inspecciona Executor.execute(), Scheduler._fire() y todos los caminos donde se persiste un evento de auditoría.

Busca:

- except ...: pass
- logging sin propagación del error;
- operaciones que continúan después de fallar EventLog.append();
- success=True generado antes de garantizar la persistencia del evento.

Implementa comportamiento fail-closed:

SI la auditoría obligatoria no puede persistirse,
ENTONCES la operación no puede considerarse exitosa.

Debe existir una excepción controlada o resultado explícito de fallo y success=False.

No ocultes el error.

Añade tests que simulen:

1. EventLog correcto → ejecución normal.
2. EventLog falla → ejecución abortada.
3. EventLog falla después de preparar el efecto → resultado fail-closed.
4. El error de persistencia queda observable.

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
FASE 1.5 — AUDITORÍA INFRANQUEABLE

Inspecciona Executor.execute(), Scheduler._fire() y todos los caminos donde se persiste un evento de auditoría.

Busca:

- except ...: pass
- logging sin propagación del error;
- operaciones que continúan después de fallar EventLog.append();
- success=True generado antes de garantizar la persistencia del evento.

Implementa comportamiento fail-closed:

SI la auditoría obligatoria no puede persistirse,
ENTONCES la operación no puede considerarse exitosa.

Debe existir una excepción controlada o resultado explícito de fallo y success=False.

No ocultes el error.

Añade tests que simulen:

1. EventLog correcto → ejecución normal.
2. EventLog falla → ejecución abortada.
3. EventLog falla después de preparar el efecto → resultado fail-closed.
4. El error de persistencia queda observable.

Ejecuta pytest.
```

## CHECKLIST
- [ ] Inspeccione repo
- [ ] No copie ciego
- [ ] Tests verdes
- [ ] Entregue STATUS etc
