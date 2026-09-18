# SPEC UPGRADE PLAN v2 - C0 a C7

> Que estamos haciendo: subir el codigo al 100% de docs/spec/* (00-20),
> sin inventar nada, sin romper el kernel, con cada fase gateada por un
> test verificable. La spec es ley. Si la spec es ambigua o contradictoria,
> se corrige la spec antes de escribir codigo.
>
> Fuentes de doctrina: docs/VISION.md, README.md, docs/STATUS.md,
> docs/INVARIANTS.md, docs/spec/00_SYSTEM_PRINCIPLES.md.
>
> Autor: sesion 2026-09-18. Sustituye al v1 (borrador superado).

## Estado del repo (confirmado contra dump y tests)

- Kernel funcional. 136 tests kernel verdes. 540 tests totales verdes.
- Ciclo Intent -> Policy -> Executor -> Tool -> EventLog operativo en
  dominios/agencia.
- 3 dominios reales (agencia, compiler, clinic) + 1 esqueleto (finance).
- Orquestador propio (orchestrator.py + loops.py + scheduler.py).
- /api/approvals y /api/missions operativos.

Fuera de alcance hasta C7:
- 44 conectores (todos connected=False, stubs).
- orchestration/temporal/* (nunca arranca en runtime).
- Supabase (solo si EVENTLOG_IMPL=supabase).

Duplicidades detectadas (a resolver en C0):
- agents/ (base + registry) vs cognition/agents/ (catalog + schemas + seed).
- execution/tools/ (13 mocks) vs connectors/providers/ (44 stubs).
- contracts/execution.Action (estricto, frozen) vs execution/action.Action
  (laxo, sin tenant_id). El Executor usa el laxo.
- kernel/ontology/metamodel.EntityCategory (5) vs
  kernel/ontology/vocabulary.entities (7 strings).
- connectors/core/capability_catalog.py importa
  cognition.planning.internal_actions -> violacion de capas.

Huecos reales (lo que spec pide y codigo no tiene):
- 18 entity types como modelos frozen (spec 03).
- 16 action verbs como enum (spec 04).
- StateMachine explicita (spec 05).
- 9 familias de microacciones vacias en spec 08.
- Referencias rotas en spec 09 (microacciones no definidas en 08).
- Nombres inconsistentes en spec 10 (RESEARCH_AGENT vs WEB_RESEARCH_AGENT).
- 3 agentes por crear (spec 10): LEAD_GENERATION, DATA_ANALYSIS, CONTENT.
  Spec declara 5. Codigo tiene 2. Total objetivo: 5.
- TaskPlan builder + scheduler topologico (spec 11).
- MissionMemory (spec 15).
- Handoff + motor de composicion (spec 19).

## Reglas nuevas (ley)

### Kernel Boundary Rule

El kernel solo puede modificarse si CUMPLE LAS CINCO:
1. Es universal (aplica a todo dominio).
2. Es necesaria para una invariante del sistema.
3. No depende de ningun dominio.
4. No introduce conocimiento de negocio.
5. Mantiene compatibilidad con los contratos existentes.

Toda modificacion del kernel entra en PR separado, con test propio,
pytest tests/kernel/ verde antes y despues, y
test_no_kernel_imports_domains verde.

### Spec Contradiction Rule

Si dos specs se contradicen, o una spec contradice el codigo sin decision
cerrada, la implementacion se detiene:

  SPEC A != SPEC B
     |
     v
  STOP
     |
     v
  decision explicita en docs/DECISIONS.md
     |
     v
  spec actualizada
     |
     v
  implementacion

Nunca el agente que escribe codigo resuelve la contradiccion implicitamente.

## Fases

### C0 - Reconciliacion y congelacion de alcance (solo docs, 2 sesiones)

Entregables:
- C0.1 docs/spec/AUDIT_MATRIX.md (matriz SPEC <-> CODIGO).
- C0.2 docs/DECISIONS.md (17 decisiones cerradas, 1 respuesta cada una).
- C0.3 docs/STATUS.md actualizado (connectors/ congelado,
  temporal/ fuera de alcance, agents/ canonicidad).
- C0.4 Extender spec 08 (9 familias), 09 (refs rotas), 10 (nombres),
  11 y 19 (contratos ejecutables).
- C0.5 Anadir a docs/spec/00 las 2 reglas nuevas.
- C0.6 Firma humana (aprobacion explicita).

Gate duro: ningun ciclo C1+ arranca sin C0.6.

### C1 - Fundamentos tipados + E2E con stub (specs 01, 03, 04, 05)

- C1a kernel/ontology/entities_catalog.py: 18 tipos frozen.
       Criterio: 18 tests, 1 por tipo, extra=forbid.
- C1b kernel/ontology/action_types.py: 16 verbos + pares prohibidos.
       Criterio: action_type=Destroy falla; (Delete, Person) falla.
- C1c kernel/ontology/context.py: 8 categorias de Context.
       Criterio: instanciable + referenciable por entity_id.
- C1d kernel/world/state_machine.py: 7 estados + transiciones.
       Criterio: PENDING->COMPLETED falla; PENDING->RUNNING->COMPLETED pasa.
- C1e Test E2E: Intent -> Policy -> Executor -> Tool stub -> EventLog.
       Criterio: caso deny + caso needs_approval verdes en
       tests/kernel/test_e2e_stub.py.

Kernel: anade (no muta) en kernel/ontology/ y kernel/world/.

### C2 - Catalogo unificado de microacciones (specs 02, 08)

- C2a docs/spec/08 - generar las 6 familias existentes desde
       capability_catalog.py + internal_actions.py. Solo doc, sin codigo.
- C2b docs/spec/08 - escribir las 9 familias vacias (DOCUMENTS, CREATIVE,
       SOCIAL, MARKETING, SOFTWARE, DATABASE, AUTOMATION, ANALYTICS +
       futuras). Cada familia con >= 5 microacciones, mismo formato que las 6.
       REQUIERE REVISION HUMANA ANTES DE MERGE. La etiqueta stub: true
       documenta el estado, no sustituye la aprobacion.
- C2c kernel/ontology/taxonomy.py: TaxonomyFamily(str, Enum).
       Criterio: taxonomy invalida falla al registrar microaccion.
- C2d Microacciones de negocio (ej. sales.score_lead) -> stub: true
       visible en JSON del catalogo.
- C2e Test: todo kind referenciado en cualquier pipeline existe en el
       catalogo generado. Mata RESEARCH_AGENT vs WEB_RESEARCH_AGENT y
       cualquier referencia rota.

Kernel: anade kernel/ontology/taxonomy.py.

### C3 - Pipeline de referencia: domains/agencia (spec 09)

- C3a domains/agencia/pipelines.py corregido para referenciar solo
       microacciones de C2.
       Criterio: test_agencia_pipelines_contract.py verde.
- C3b Ejecucion E2E de leads_to_draft con Executor + stub.
       Criterio: draft generado + EventLog con PipelineStarted/Completed.

Kernel: no toca.

### C4 - Catalogo de agentes (spec 10, transcripcion literal)

- C4a Fusion agents/ -> cognition/agents/ segun decision D11 de C0.2.
       Un solo modulo canonico. El otro marcado deprecated.
- C4b Los 5 agentes de spec 10 implementados:
       WEB_RESEARCH_AGENT, LEAD_GENERATION_AGENT, COMMUNICATION_AGENT,
       DATA_ANALYSIS_AGENT, CONTENT_AGENT.
       Criterio: 5/5 con MiniAgentSchema valido.
- C4c Handoffs verificados bidireccionalmente.
       Criterio: todo handoff declarado existe en el otro lado.

Kernel: no toca.

### C5 - Bucle agentico completo (specs 09, 11, 15, 19)

- C5a orchestration/planner.py: build_task_plan(intent, catalog) -> TaskPlan.
       Criterio: Intent produce TaskPlan con nodos correctos.
- C5b kernel/world/mission_memory.py.
       Criterio: TaskPlan ejecutado produce MissionMemory reconstruible
       del EventLog.
- C5c orchestration/approvals.py: pausa real + reanudacion.
       Criterio: POST /api/approvals/{id}/decision reanuda el nodo.
- C5d Test E2E: mensaje conversacional -> TaskPlan -> ejecucion -> EventLog.
       Criterio: un comando de usuario genera traza completa.

Kernel: anade kernel/world/mission_memory.py.

### C6 - Sandbox con 3 empresas ficticias

- 3 dominios (agencia, clinic, compiler) ejecutando pipelines de punta a
  punta con stub. Criterio: los 3 corren en una sesion, sin red.

Kernel: no toca.

### C7 - Conectores reales + Temporal + Supabase (al final)

- Uno a uno, sustituyendo stubs por providers reales.
- Contratos ActionSpec, ExecutionResult, Command NO cambian entre stub y
  real. Este ciclo es barato porque C0-C6 fijan los contratos.

Kernel: no toca.

## Lo que NO se hace

- No inventar microacciones (spec 00).
- No implementar spec 09 sin spec 08 completa (Spec Contradiction Rule).
- No tocar kernel/ sin PR separado + test + Kernel Boundary Rule.
- No tocar orchestration/temporal/, connectors/providers/ reales, ni
  Supabase hasta C7.
- No mergear sin pytest verde.
- No permitir que el agente que escribe codigo resuelva contradicciones
  de spec implicitamente.
- No archivar audits sin verificar cierre real.

## Volumen

- C0: 2 sesiones (docs).
- C1: 1 sesion (codigo + tests).
- C2: 3-4 sesiones (el mas grande).
- C3: 1 sesion.
- C4: 1 sesion.
- C5: 2 sesiones.
- C6: 1 sesion.
- C7: incremental, fuera de este plan.

Total hasta C6: 11-12 sesiones.

## Mantenimiento

- Al cerrar cada ciclo, anotar aqui:
  Ciclo N cerrado (YYYY-MM-DD, commits X..Y).
- Sub-ciclos como C2a, C2b.
- Decisiones nuevas a docs/DECISIONS.md.

