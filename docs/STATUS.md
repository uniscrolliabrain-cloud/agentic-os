# STATUS — Estado real del proyecto

> Fuente de verdad operativa: qué promete la spec y qué está implementado HOY.
> Se actualiza en cada PR que toque `kernel/`, `connectors/`, `orchestration/`
> o `interfaces/`.
>
> Documentos relacionados:
> - Visión: `docs/VISION.md`
> - Arquitectura: `docs/ARCHITECTURE.md`
> - Invariantes: `docs/INVARIANTS.md`
> - Auditoría vigente: `docs/audits/KERNEL_INVARIANTS.md`
> - Checklist pre-producción: `docs/PRE_PRODUCTION_CHECKLIST.md`

## Leyenda

| Símbolo | Significado |
|---|---|
| OK | Implementado y testeado |
| PARCIAL | Parcial / con caveat |
| NO | Declarado en spec, no implementado |

## 1. Kernel

| Componente | Fuente | Estado | Nota |
|---|---|---|---|
| Event inmutable | INVARIANTS.md:10 | OK | KernelModel frozen |
| EventLog append-only | INVARIANTS.md:11 | PARCIAL | `events` es lista publica mutable (AUD-07) |
| WorldState derivable por replay | INVARIANTS.md:12 | OK | Todos los kinds manejados o no-op explicito (AUD-04 resuelto) |
| apply() puro | INVARIANTS.md:13 | OK | |
| CorruptEventError (fail-closed) | INVARIANTS.md:15 | OK | AUD-04 resuelto |
| Policy inmutable | INVARIANTS.md:22 | OK | |
| Deny by default | INVARIANTS.md:23 | OK | AUD-11 resuelto |
| Engine pure | INVARIANTS.md:25 | OK | AUD-02 resuelto (policies_dir inyectable) |
| Delete/Publish -> approval | INVARIANTS.md:26 | OK | AUD-11 resuelto (DEV_ALLOW_ALL pasa por evaluador) |
| DEFAULT_VOCAB inmutable | INVARIANTS.md:34 | NO | Los set internos son mutables (AUD-08) |
| Kernel no importa fuera | tests/kernel/test_no_kernel_imports_domains.py | OK | AUD-01 resuelto (tenant_resolver inyectable + test robusto) |

## 2. Cognition

| Componente | Fuente | Estado |
|---|---|---|
| 4 memorias por (tenant, agente) | docs/COGNITION.md | OK |
| MiniAgentSchema (25 campos) | 07_PYDANTIC_CONTRACTS.md | OK |
| Catalogo de agentes (5 en spec, 2 impl.) | 10_AGENT_CATALOG.md | PARCIAL |
| TaskPlan con validacion DAG | 07 | OK |

## 3. Execution

| Componente | Fuente | Estado | Nota |
|---|---|---|---|
| Executor gobernado por policy | docs/GOVERNANCE.md | OK | |
| Contrato unico de error de tools | tests/security/test_hardening_fase3.py | OK | |
| Executor.execute_action() usa tenant del contexto | docs/audits/PERMISSIONS.md GAP 1 | NO | Fuerza tenant_id="system" (AUD-16) |

## 4. Connectors

| Componente | Fuente | Estado | Nota |
|---|---|---|---|
| Providers declarados | README.md | OK | 45 (README dice 44 - desactualizado) |
| Mappings provider -> capability | README.md | OK | 286 (README dice 265) |
| Capabilities canonicas unicas | README.md | OK | 203 (README dice ~187) |
| Providers sin conectar por defecto | README.md | OK | StubConnector con connected=False |
| Google real tras flag | settings.google_real | OK | Doble gate: flag + credenciales |
| Risk classes (READ_ONLY/EXTERNAL/FINANCIAL/DESTRUCTIVE) | README.md | PARCIAL | Solo delete/publish endurecen (AUD-13) |

## 5. Orchestration

| Componente | Fuente | Estado | Nota |
|---|---|---|---|
| Intent -> Policy -> Executor -> EventLog | README.md | OK | |
| PipelineRunner tenant-agnostico | domains/*/pipelines.py | OK | Despacho por DomainRegistry |
| run_pipeline (Intent -> PipelineRunner) | tests/orchestration/test_run_pipeline.py | OK | |
| correlation_id end-to-end | docs/audits/OBSERVABILITY.md | PARCIAL | Se pierde en Executor._audit() |
| Scheduler inyecta TenantContext | docs/audits/PERMISSIONS.md GAP 2 | NO | Policy saltado en tareas programadas |

## 6. Interfaces

| Endpoint | Fuente | Estado |
|---|---|---|
| POST /api/v1/chat | README.md | OK |
| GET /api/v1/events, /state, /tasks | README.md | OK |
| POST /api/v1/execute | README.md | OK |
| CRUD /api/v1/tenants, /conversations | README.md | OK |
| GET /api/v1/skills, /tools | README.md | OK |
| POST /api/v1/approvals/* | 14_HUMAN_APPROVAL.md | NO |
| GET /api/v1/missions, /missions/{id}/trace | 17_OBSERVABILITY.md | NO |
| /api/v1/tenants/{id}/chat (compilador) | PLAN_CLINE_AGENTE_COMPILADOR | OK |

## 7. Dominios

| Dominio | Estado |
|---|---|
| bor-agencia | OK - 7 entidades, 3 pipelines, 3 SOPs |
| agentic-compiler | OK - 3 entidades, 2 pipelines (deshabilitados por diseno) |
| clinic | PARCIAL - Solo ontologia |
| finance | PARCIAL - Solo vocabulario |
| _examples | OK - 9 entidades de test/demo |

## 8. Deuda tecnica priorizada

### Bloqueantes (rompen la ley del kernel)
- AUD-01: kernel importa infrastructure.tenancy
- AUD-02: PolicyEngine.decide() no es pura
- AUD-03: tenant_id sin validar en ruta
- AUD-04: perdida silenciosa de eventos
- AUD-11: DEV_ALLOW_ALL bypassa PolicyEvaluator

### Altos
- Endpoints /api/approvals y /api/missions no existen
- correlation_id se pierde en Executor._audit()
- Scheduler no inyecta TenantContext
- README desactualizado (frontend, 44->45 providers, 265->286, 187->203)

### Medios
- scripts/audit.sh no puede pasar en verde (AUD-19)
- tests/bugs/ citado pero no existe (vive en tests/agent-notes/bugs/)
- Tres representaciones de Action (AUD-15)
- data/policies/*.json versionado en git (AUD-22)

## Como mantener este fichero

1. En cada PR que toque kernel/, connectors/, orchestration/ o interfaces/,
   actualizar la fila correspondiente.
2. Cuando un hallazgo de docs/audits/KERNEL_INVARIANTS.md se resuelva, moverlo
   de "Deuda tecnica" a "Implementado".
3. Nunca marcar OK sin un test que lo cubra.

## Cobertura spec vs realidad

> Estimacion de cuanto de cada fichero de `docs/spec/` esta implementado en
> codigo. No es una medida exacta: refleja el grado de alineacion funcional.
> Se revisa 1 vez por ciclo de hardening.

### Vinculantes (implementados, contrato activo)

| Fichero | % | Nota |
|---|---|---|
| `00_SYSTEM_PRINCIPLES.md` | 100% | Ley del sistema, aplicada en kernel y orquestador |
| `07_PYDANTIC_CONTRACTS.md` | 100% | Schemas reales en cognition/agents/schemas.py |
| `13_PERMISSIONS.md` | 95% | PolicyEngine real, AUD-12 resuelto |
| `14_HUMAN_APPROVAL.md` | 80% | Endpoints + EventLog; falta "pausa/reanudacion de pipeline" |
| `17_OBSERVABILITY.md` | 85% | Endpoints + EventLog; falta correlation_id end-to-end |

### Aspiracionales (diseno declarado, no implementado)

| Fichero | % | Nota |
|---|---|---|
| `01_ONTOLOGY.md` | 90% | Metamodelo implementado; falta conectar al runtime (AUD-09) |
| `02_TAXONOMY.md` | 40% | 15 familias declaradas; 6 con catalogo completo |
| `03_ENTITY_TYPES.md` | 60% | Tipos reales en `_examples/` + dominios reales |
| `04_ACTION_TYPES.md` | 70% | Verbos canonicos usados en capabilities |
| `05_STATE_MACHINE.md` | 20% | Estados narrativos; no hay `StateMachine` ejecutable |
| `06_TOOL_TAXONOMY.md` | 70% | Tools nativas + connector bridge; faltan adapters API/MCP declarados |
| `08_MICROACTION_CATALOG.md` | 45% | 6 familias completas; 9 esbozadas |
| `09_PIPELINE_CATALOG.md` | 15% | Los 5 pipelines declarados NO existen; los reales son por tenant |
| `10_AGENT_CATALOG.md` | 40% | 2 de 5 agentes implementados; ninguno se ejecuta desde el orquestador |
| `11_ORCHESTRATION.md` | 60% | Router determinista + LLM; TaskGraph/DAG declarado, no construido |
| `12_ERROR_HANDLING.md` | 50% | RetryEngine existe; no se aplica a microacciones/pipelines |
| `15_MEMORY_AND_STATE.md` | 70% | 4 memorias por (tenant, agente); falta `MissionMemory` |
| `16_VALIDATION.md` | 50% | Pydantic valida entidades; no hay validacion por paso de pipeline |
| `18_TESTING.md` | 85% | Suite completa + agent-notes/bugs; falta cobertura por agente del catalogo |
| `19_AGENT_COMPOSITION.md` | 30% | Modelo `handoffs` existe; no hay motor de handoff |
| `20_CLINE_IMPLEMENTATION_PROTOCOL.md` | 80% | Protocolo aplicado; fases 3-4 pendientes (compilador) |

### Promedio

- **Vinculantes:** ~92%
- **Aspiracionales:** ~55%
- **Global ponderado:** ~70%

El objetivo del ciclo E es reducir la brecha marcando cada fichero aspiracional con `status: diseno` en su cabecera, para que ningun contributor confunda spec con codigo.

---

## Como mantener esta seccion

1. Se actualiza 1 vez por ciclo de hardening (no en cada PR).
2. Cuando un fichero pase de aspiracional a vinculante, moverlo de tabla.
3. Si el porcentaje cambia +/- 10 puntos, actualizar la fila.

## Deuda con decision tomada

Elementos de auditoria que NO se van a resolver con codigo: se cierran
con una decision documentada.

### AUD-15 — Action / ExecutionResult duplicados

**Situacion:** 2 definiciones de Action y 2 de ExecutionResult:

- contracts/execution.py → estrictas (canonicas).
- execution/action.py y execution/result.py → laxas (legacy).

**Quien las usa:** las estrictas SOLO las usan 2 tests
(	ests/kernel/test_contracts.py, 	ests/kernel/test_execution_contracts.py).
Las laxas las usa executor.py.

**Decision:** NO unificar hoy. El refactor del Executor para usar
ActionParams tipado y devolver ExecutionResult con output_keys
(no output: dict) toca ~15 sitios y no aporta funcionalidad nueva.
Se documenta la co-existencia con docstrings claros en los 3 ficheros.

**Reabrir si:** se necesita auditabilidad fina de salidas del Executor
(no filtrar valores) o se desea eliminar la clase laxa por completitud.

### GAPs de los audits internos (Observability, Permissions)

Los 3 GAPs documentados en docs/audits/OBSERVABILITY.md y
docs/audits/PERMISSIONS.md (correlation_id, TenantContext en scheduler,
doble path de decision) fueron resueltos por el hardening de los commits
26881e4, 8bde3a y ae89b8. Los audits se actualizan con la marca
de RESUELTO.

La seccion "Cobertura spec vs realidad" refleja el estado actual.

### AUD-05 — event_type/data (camino tipado) sin productor

**Situacion:** el modelo `Event` del kernel define `event_type: Optional[str]`
y `data: Optional[T]` como camino tipado alternativo a `kind`/`payload`. En
el codigo real **no hay ningun productor**: todos los `event_type=` de
`src/` pertenecen a OTROS modelos (`EpisodicEvent`, `WebhookEvent`,
`TelemetryEvent`), no al `Event` del kernel.

**Consumidores:** `kernel/world/events.py:78,84,86,91` (validacion interna
del propio campo) y `interfaces/api/missions.py:51,78` (fallback defensivo
`e.kind or e.event_type`). Ninguno depende de que `event_type` este
poblado.

**Decision:** documentar el camino tipado como **legacy sin productor** en
el propio `events.py`. Se conserva porque:
1. Los tests lo ejercen (`test_worldstate_typed` usa `event.data`).
2. Un cliente externo podria construir `Event(event_type=..., data=...)`.

**Reabrir si:** se decide unificar en un solo camino de eventos. Entonces
se eliminaria `event_type`/`data` y se migrarian los tests.

### AUD-09 — OntologyBundle desconectado del runtime

**Situacion:** `OntologyBundle` se produce en `validate_against_metamodel`
y se consume en `domains/base.py::compile_ontology`. Pero `WorldState` y
`kernel/world/applier.py` **no lo consultan**: el guard real de entidades
es `ENTITY_TYPE_REGISTRY`.

**Decision:** documentar `OntologyBundle` como artefacto de **design-time**
(validacion fail-closed en bootstrap), no guard de runtime. Esto es
correcto para el modelo actual: la ontologia se valida una vez al
registrar el dominio y no se revalida por cada evento.

**Reabrir si:** se quiere hacer cumplir el vocabulario del tenant en
runtime (p.ej. un evento `entity_created` con `kind` fuera del bundle del
tenant deberia fallar). Requiere inyectar el bundle en `WorldState` y
`applier`, decision de diseño grande.

### AUD-10 — ENTITY_TYPE_REGISTRY global del proceso

**Situacion:** el registro de tipos de entidad es un `dict` a nivel de
modulo en `kernel/ontology/domain_models.py`. No esta scoped por tenant.

**Decision:** documentar como **global del proceso**. Suficiente para:
- Deploy 1-tenant-por-proceso (aislamiento trivial).
- Deploy multi-tenant donde los dominios registrados no colisionan
  (agencia + compiler + clinic + finance conviven sin solaparse).

**No se scop por tenant porque:**
1. Requiere refactor de `entity_from_payload` y `apply`.
2. Los tests actuales lo resetean con fixture (no dependen del scope).
3. No hay caso de uso real hoy con dos tenants que usen el mismo
   `kind` con definiciones distintas.

**Reabrir si:** aparece un caso de uso donde dos tenants necesiten el
mismo `kind` con esquemas distintos. Entonces hay que hacer
`EntityRegistry` por tenant y cambiarlo todo.

---

## Estado tras Ciclo D

- AUD-05, AUD-09, AUD-10: **cerrados por decision documentada**.
- Total AUD cerrados: **17 de 22** (14 fix + 3 decision).

Pendientes: AUD-17, 18 (probablemente resueltos, verificar), AUD-20
(deriva documental menor), AUD-22 (decision sobre policies versionadas).