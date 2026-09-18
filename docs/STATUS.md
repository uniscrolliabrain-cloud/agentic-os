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
| WorldState derivable por replay | INVARIANTS.md:12 | PARCIAL | Solo los 4 kind reconocidos (AUD-04) |
| apply() puro | INVARIANTS.md:13 | OK | |
| CorruptEventError (fail-closed) | INVARIANTS.md:15 | PARCIAL | AUD-04 |
| Policy inmutable | INVARIANTS.md:22 | OK | |
| Deny by default | INVARIANTS.md:23 | PARCIAL | DEV_ALLOW_ALL corta antes del evaluador (AUD-11) |
| Engine pure | INVARIANTS.md:25 | NO | I/O de disco + CWD-dependiente (AUD-02) |
| Delete/Publish -> approval | INVARIANTS.md:26 | PARCIAL | AUD-11 |
| DEFAULT_VOCAB inmutable | INVARIANTS.md:34 | NO | Los set internos son mutables (AUD-08) |
| Kernel no importa fuera | tests/kernel/test_no_kernel_imports_domains.py | NO | policy/engine.py:73 importa infrastructure.tenancy (AUD-01) |

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