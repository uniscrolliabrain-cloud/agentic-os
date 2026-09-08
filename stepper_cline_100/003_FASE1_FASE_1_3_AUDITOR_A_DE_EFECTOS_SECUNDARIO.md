# 003/100 - FASE 1.3 — AUDITORÍA DE EFECTOS SECUNDARIOS
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
# TAREA 003/100 - FASE 1.3 — AUDITORÍA DE EFECTOS SECUNDARIOS

## PROTOCOLO OBLIGATORIO ANTES DE CODIFICAR
1. Lee el estado REAL del repo: inspecciona src/, tests/, imports actuales.
2. No copies código de la especificación ciegamente. Si ya existe implementación superior, consérvala y adapta.
3. Localiza tests relacionados antes de tocar código.
4. No introduzcas pass, TODO, ..., Any, type: ignore, except: pass ni bypasses.

## CONTEXTO ARQUITECTÓNICO
Fase 1: SANITIZACIÓN Y CIMENTACIÓN DEL KERNEL
Invariante clave: LLM != Executor, Agent != Connector, Text != Command, Command != Permission. Todo efecto externo pasa por UserContext -> Policy -> Command -> Executor -> ConnectorRouter -> Connector.

## TU TAREA ESPECÍFICA
FASE 1.3 — AUDITORÍA DE EFECTOS SECUNDARIOS

Busca en todo src/agentic_os cualquier llamada que pueda producir efectos externos sin pasar por el Executor.

Busca explícitamente:

- tool.run(
- connector.execute(
- provider.execute(
- requests realizadas desde capas de orquestación;
- llamadas SDK realizadas fuera de connectors/providers;
- acceso directo a APIs externas desde agents/orchestrator/pipelines.

Clasifica cada aparición:

A) legítima porque pertenece a un connector/provider;
B) legítima porque es infraestructura;
C) bypass arquitectónico que debe eliminarse.

Corrige únicamente los casos B/C que vulneren la frontera arquitectónica.

La regla es:

LLM/agente/orquestador NO ejecuta APIs externas.
El Kernel/Executor controla la syscall.
Los connectors son el único lugar donde se materializa el efecto externo.

Crea tests de regresión para los bypass encontrados.

Ejecuta pytest.

No hagas todavía modificaciones de ontología, SMC, identidad ni Model Mesh.

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
FASE 1.3 — AUDITORÍA DE EFECTOS SECUNDARIOS

Busca en todo src/agentic_os cualquier llamada que pueda producir efectos externos sin pasar por el Executor.

Busca explícitamente:

- tool.run(
- connector.execute(
- provider.execute(
- requests realizadas desde capas de orquestación;
- llamadas SDK realizadas fuera de connectors/providers;
- acceso directo a APIs externas desde agents/orchestrator/pipelines.

Clasifica cada aparición:

A) legítima porque pertenece a un connector/provider;
B) legítima porque es infraestructura;
C) bypass arquitectónico que debe eliminarse.

Corrige únicamente los casos B/C que vulneren la frontera arquitectónica.

La regla es:

LLM/agente/orquestador NO ejecuta APIs externas.
El Kernel/Executor controla la syscall.
Los connectors son el único lugar donde se materializa el efecto externo.

Crea tests de regresión para los bypass encontrados.

Ejecuta pytest.

No hagas todavía modificaciones de ontología, SMC, identidad ni Model Mesh.
```

## CHECKLIST
- [ ] Inspeccione repo
- [ ] No copie ciego
- [ ] Tests verdes
- [ ] Entregue STATUS etc
