# 092/100 - FASE 10.2 — REPOSITORIO LIMPIO
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
# TAREA 092/100 - FASE 10.2 — REPOSITORIO LIMPIO

## PROTOCOLO OBLIGATORIO ANTES DE CODIFICAR
1. Lee el estado REAL del repo: inspecciona src/, tests/, imports actuales.
2. No copies código de la especificación ciegamente. Si ya existe implementación superior, consérvala y adapta.
3. Localiza tests relacionados antes de tocar código.
4. No introduzcas pass, TODO, ..., Any, type: ignore, except: pass ni bypasses.

## CONTEXTO ARQUITECTÓNICO
Fase 10: HARDENING FINAL, TESTS Y PRODUCCIÓN
Invariante clave: LLM != Executor, Agent != Connector, Text != Command, Command != Permission. Todo efecto externo pasa por UserContext -> Policy -> Command -> Executor -> ConnectorRouter -> Connector.

## TU TAREA ESPECÍFICA
FASE 10.2 — REPOSITORIO LIMPIO

Audita .gitignore.

Debe excluir como mínimo:

.env
.env.*
.credentials/
data/creds/
data/eventlog/
data/tenants/
data/policies/
__pycache__/
.pytest_cache/
.ruff_cache/
.mypy_cache/
.vscode/
.idea/
build/
dist/
*.egg-info

Conserva .env.example.

Busca secretos reales en el working tree y git history reciente.

NO borres información sin informar.

Si encuentras un secreto versionado, detén el paso y reporta el riesgo.

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
FASE 10.2 — REPOSITORIO LIMPIO

Audita .gitignore.

Debe excluir como mínimo:

.env
.env.*
.credentials/
data/creds/
data/eventlog/
data/tenants/
data/policies/
__pycache__/
.pytest_cache/
.ruff_cache/
.mypy_cache/
.vscode/
.idea/
build/
dist/
*.egg-info

Conserva .env.example.

Busca secretos reales en el working tree y git history reciente.

NO borres información sin informar.

Si encuentras un secreto versionado, detén el paso y reporta el riesgo.
```

## CHECKLIST
- [ ] Inspeccione repo
- [ ] No copie ciego
- [ ] Tests verdes
- [ ] Entregue STATUS etc
