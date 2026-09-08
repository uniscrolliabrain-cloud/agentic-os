# 027/100 - FASE 3.7 — REPROMPT AUTOCORRECTIVO
FASE 3 - SEMANTIC MISSION COMPILER
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
# TAREA 027/100 - FASE 3.7 — REPROMPT AUTOCORRECTIVO

## PROTOCOLO OBLIGATORIO ANTES DE CODIFICAR
1. Lee el estado REAL del repo: inspecciona src/, tests/, imports actuales.
2. No copies código de la especificación ciegamente. Si ya existe implementación superior, consérvala y adapta.
3. Localiza tests relacionados antes de tocar código.
4. No introduzcas pass, TODO, ..., Any, type: ignore, except: pass ni bypasses.

## CONTEXTO ARQUITECTÓNICO
Fase 3: SEMANTIC MISSION COMPILER
Invariante clave: LLM != Executor, Agent != Connector, Text != Command, Command != Permission. Todo efecto externo pasa por UserContext -> Policy -> Command -> Executor -> ConnectorRouter -> Connector.

## TU TAREA ESPECÍFICA
FASE 3.7 — REPROMPT AUTOCORRECTIVO

Implementa el bucle de cristalización de máximo dos intentos según la especificación.

Si Pydantic devuelve ValidationError:

1. extrae e.errors();
2. construye un feedback contractual;
3. envía nuevamente al router;
4. valida otra vez.

No incluyas traceback interno innecesario, secretos o datos sensibles en el prompt.

Si el segundo intento falla:

- devuelve None o resultado contractual de clarificación;
- no ejecutes nada.

Añade tests:

- primer intento correcto;
- primer intento inválido + segundo correcto;
- ambos inválidos;
- fallo de infraestructura.

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
FASE 3.7 — REPROMPT AUTOCORRECTIVO

Implementa el bucle de cristalización de máximo dos intentos según la especificación.

Si Pydantic devuelve ValidationError:

1. extrae e.errors();
2. construye un feedback contractual;
3. envía nuevamente al router;
4. valida otra vez.

No incluyas traceback interno innecesario, secretos o datos sensibles en el prompt.

Si el segundo intento falla:

- devuelve None o resultado contractual de clarificación;
- no ejecutes nada.

Añade tests:

- primer intento correcto;
- primer intento inválido + segundo correcto;
- ambos inválidos;
- fallo de infraestructura.

Ejecuta pytest.
```

## CHECKLIST
- [ ] Inspeccione repo
- [ ] No copie ciego
- [ ] Tests verdes
- [ ] Entregue STATUS etc
