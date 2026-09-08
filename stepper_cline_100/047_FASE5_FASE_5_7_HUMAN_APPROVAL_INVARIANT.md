# 047/100 - FASE 5.7 — HUMAN APPROVAL INVARIANT
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
# TAREA 047/100 - FASE 5.7 — HUMAN APPROVAL INVARIANT

## PROTOCOLO OBLIGATORIO ANTES DE CODIFICAR
1. Lee el estado REAL del repo: inspecciona src/, tests/, imports actuales.
2. No copies código de la especificación ciegamente. Si ya existe implementación superior, consérvala y adapta.
3. Localiza tests relacionados antes de tocar código.
4. No introduzcas pass, TODO, ..., Any, type: ignore, except: pass ni bypasses.

## CONTEXTO ARQUITECTÓNICO
Fase 5: IDENTIDAD, MULTI-TENANCY Y POLICY ENGINE
Invariante clave: LLM != Executor, Agent != Connector, Text != Command, Command != Permission. Todo efecto externo pasa por UserContext -> Policy -> Command -> Executor -> ConnectorRouter -> Connector.

## TU TAREA ESPECÍFICA
FASE 5.7 — HUMAN APPROVAL INVARIANT

Implementa la invariante descrita:

operaciones delete y publish no pueden ser permitidas automáticamente cuando la policy exige aprobación humana.

La decisión debe distinguir:

allow
deny
require_approval

No confíes en que el LLM respete esta regla.

La comprobación debe ocurrir en el kernel/policy layer.

Añade tests intentando:

delete;
publish;
wildcard delete;
wildcard publish;
roles no autorizados.

Todos deben respetar default-deny y aprobación.

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
FASE 5.7 — HUMAN APPROVAL INVARIANT

Implementa la invariante descrita:

operaciones delete y publish no pueden ser permitidas automáticamente cuando la policy exige aprobación humana.

La decisión debe distinguir:

allow
deny
require_approval

No confíes en que el LLM respete esta regla.

La comprobación debe ocurrir en el kernel/policy layer.

Añade tests intentando:

delete;
publish;
wildcard delete;
wildcard publish;
roles no autorizados.

Todos deben respetar default-deny y aprobación.
```

## CHECKLIST
- [ ] Inspeccione repo
- [ ] No copie ciego
- [ ] Tests verdes
- [ ] Entregue STATUS etc
