# 012/100 - FASE 2.2 — BASE FÍSICA DE ENTIDADES
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
# TAREA 012/100 - FASE 2.2 — BASE FÍSICA DE ENTIDADES

## PROTOCOLO OBLIGATORIO ANTES DE CODIFICAR
1. Lee el estado REAL del repo: inspecciona src/, tests/, imports actuales.
2. No copies código de la especificación ciegamente. Si ya existe implementación superior, consérvala y adapta.
3. Localiza tests relacionados antes de tocar código.
4. No introduzcas pass, TODO, ..., Any, type: ignore, except: pass ni bypasses.

## CONTEXTO ARQUITECTÓNICO
Fase 2: ONTOLOGÍA TIPADA Y WORLDSTATE
Invariante clave: LLM != Executor, Agent != Connector, Text != Command, Command != Permission. Todo efecto externo pasa por UserContext -> Policy -> Command -> Executor -> ConnectorRouter -> Connector.

## TU TAREA ESPECÍFICA
FASE 2.2 — BASE FÍSICA DE ENTIDADES

Implementa o consolida:

src/agentic_os/kernel/ontology/domain_models.py

Debe existir una base DomainEntity Pydantic v2 con:

- frozen=True
- extra="forbid"
- validate_assignment=True
- comportamiento consistente con el Kernel.

Debe ser imposible introducir atributos arbitrarios.

Conserva la abstracción KernelModel si la arquitectura existente exige que DomainEntity herede de ella.

No dupliques dos bases incompatibles.

Añade tests que demuestren:

- creación válida;
- campo desconocido rechazado;
- mutación rechazada;
- serialización válida;
- validación Pydantic v2.

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
FASE 2.2 — BASE FÍSICA DE ENTIDADES

Implementa o consolida:

src/agentic_os/kernel/ontology/domain_models.py

Debe existir una base DomainEntity Pydantic v2 con:

- frozen=True
- extra="forbid"
- validate_assignment=True
- comportamiento consistente con el Kernel.

Debe ser imposible introducir atributos arbitrarios.

Conserva la abstracción KernelModel si la arquitectura existente exige que DomainEntity herede de ella.

No dupliques dos bases incompatibles.

Añade tests que demuestren:

- creación válida;
- campo desconocido rechazado;
- mutación rechazada;
- serialización válida;
- validación Pydantic v2.

Ejecuta pytest.
```

## CHECKLIST
- [ ] Inspeccione repo
- [ ] No copie ciego
- [ ] Tests verdes
- [ ] Entregue STATUS etc
