# AUDIT MATRIX - SPEC <-> CODIGO

> Matriz de reconciliacion. Se rellena en C0.1 y se mantiene viva
> durante C1-C7. Una fila por concepto. Si una fila cambia de estado,
> se anota en el commit correspondiente.
>
> Columnas: Spec | Concepto | Codigo actual | Ubicacion correcta | Estado.
>
> Estados:
> - OK: codigo y spec alineados.
> - FALTA: spec lo pide, codigo no lo tiene.
> - DUPLICADO: dos representaciones del mismo concepto, sin jerarquia.
> - CONTRADICCION: spec y codigo se contradicen, o dos specs entre si.
> - HUECO_SPEC: la spec no define el concepto lo suficiente para implementarlo.

## Entidades y tipos base

| Spec | Concepto | Codigo actual | Ubicacion correcta | Estado |
|---|---|---|---|---|
| 03 | 18 entity types | entities_catalog.py (C1a) | kernel/ontology/entities_catalog.py | OK |
| 03 | Namespace de entity kinds | core.* aplicado (C1a) | docs/DECISIONS.md D03 | OK |
| 01 | EntityCategory (metamodelo) | metamodel.EntityCategory (5) | kernel/ontology/metamodel.py | OK |
| 01 | Vocabulary.entities | vocabulary.entities (7 strings) | kernel/ontology/vocabulary.py | OK |
| 04 | 16 action verbs | action_types.py (C1b) | kernel/ontology/action_types.py | OK |
| 04 | Pares (Action, Entity) prohibidos | FORBIDDEN_ACTION_ENTITY_PAIRS (C1b) | kernel/ontology/action_types.py | OK |
| 01 | Context (8 categorias) | context.py (C1c) | kernel/ontology/context.py | OK |
| 01 | EntityRef | kernel/ontology/entities.py | kernel/ontology/entities.py | OK |
| 01 | Entity[Generic[T]] | kernel/ontology/entities.py | kernel/ontology/entities.py | OK |

## Estado y ciclo de vida

| Spec | Concepto | Codigo actual | Ubicacion correcta | Estado |
|---|---|---|---|---|
| 05 | StateMachine (7 estados) | state_machine.py (C1d) | kernel/world/state_machine.py | OK |
| 05 | TaskNode.state | TaskNode.status: str | cognition/agents/schemas.py | FALTA |
| 05 | Evento StateTransitioned | No se emite | kernel/world/events.py | FALTA |
| 12 | retry_policy por microaccion | No se aplica en runner | orchestration/pipelines/runner.py | FALTA |
| 12 | timeout_seconds por step | No se aplica | orchestration/pipelines/runner.py | FALTA |
| 12 | MicroActionFailed evento | No se emite | orchestration/pipelines/runner.py | FALTA |

## Microacciones y pipelines

| Spec | Concepto | Codigo actual | Ubicacion correcta | Estado |
|---|---|---|---|---|
| 08 | 6 familias documentadas | MicroActionSchema en seed.py (parcial) | cognition/agents/microactions/ | FALTA |
| 08 | 9 familias vacias (DOCUMENTS, CREATIVE, ...) | No existen | docs/spec/08 + cognition/agents/microactions/ | HUECO_SPEC |
| 02 | TaxonomyFamily (15 + futuras) | taxonomy.py (C2c) | kernel/ontology/taxonomy.py | OK |
| 08 | Microacciones de negocio como stub | No definidas | cognition/agents/microactions/ | HUECO_SPEC |
| 09 | 5 pipelines de sistema | No existen | orchestration/pipelines/catalog/ | FALTA |
| 09 | Referencias rotas a microacciones inexistentes | research.extract_company_data, sales.score_lead, ... | docs/spec/09 | CONTRADICCION |
| 07 | MicroActionSchema | cognition/agents/schemas.py | OK | OK |
| 07 | PipelineSchema | cognition/agents/schemas.py | OK | OK |
| 07 | TaskNode / TaskPlan | cognition/agents/schemas.py | OK | OK |

## Agentes y composicion

| Spec | Concepto | Codigo actual | Ubicacion correcta | Estado |
|---|---|---|---|---|
| 10 | WEB_RESEARCH_AGENT | web_research_agent (seed.py) | cognition/agents/ | OK |
| 10 | COMMUNICATION_AGENT | communication_agent (seed.py) | cognition/agents/ | OK |
| 10 | LEAD_GENERATION_AGENT | No existe | cognition/agents/ | FALTA |
| 10 | DATA_ANALYSIS_AGENT | No existe | cognition/agents/ | FALTA |
| 10 | CONTENT_AGENT | No existe | cognition/agents/ | FALTA |
| 10 | Nombre RESEARCH_AGENT vs WEB_RESEARCH_AGENT | Referencia rota en spec 10 | docs/spec/10 | CONTRADICCION |
| 19 | Handoff schema | No existe | cognition/agents/schemas.py | FALTA |
| 19 | resolve_handoffs(plan) | No existe | cognition/agents/composition.py | FALTA |
| 10 | agents/ vs cognition/agents/ | Ambos existen | docs/DECISIONS.md D11 | DUPLICADO |

## Orquestacion

| Spec | Concepto | Codigo actual | Ubicacion correcta | Estado |
|---|---|---|---|---|
| 11 | build_task_plan(intent, catalog) | No existe | orchestration/planner.py | FALTA |
| 11 | task_scheduler (topologico) | No existe | orchestration/task_scheduler.py | FALTA |
| 11 | Serializacion TaskPlan -> TaskNode[] | No definida | docs/spec/11 | HUECO_SPEC |
| 14 | ApprovalGate pausa + reanudacion | /api/approvals existe (parcial) | orchestration/approvals.py | FALTA |

## Memoria

| Spec | Concepto | Codigo actual | Ubicacion correcta | Estado |
|---|---|---|---|---|
| 15 | MissionMemory | No existe | kernel/world/mission_memory.py | FALTA |
| 15 | EventRef, Fact | No existen | kernel/world/mission_memory.py | FALTA |
| 15 | cognition/memory/ 4 memorias | CognitionStore completo | cognition/memory/ | OK |

## Kernel y contratos (higiene)

| Spec | Concepto | Codigo actual | Ubicacion correcta | Estado |
|---|---|---|---|---|
| 07 | contracts.execution.Action | frozen, extra=forbid | Contract canonico (si D17) | DUPLICADO |
| 07 | execution.action.Action | laxo, sin tenant_id | Deprecated si D17 | DUPLICADO |
| 07 | contracts.execution.ExecutionResult | estricto | Contract canonico | OK |
| 07 | execution.result.ExecutionResult | laxo | Deprecated si D17 | DUPLICADO |
| 00 | Kernel no importa fuera del kernel | engine.py usa infra.tenancy | mitigado por AUD-01 | OK (mitigado) |
| 00 | Deny by default | PolicyEvaluator correcto | kernel/policy/evaluator.py | OK |
| 00 | Delete/Publish -> require_approval | ampliado (AUD-13) | kernel/policy/evaluator.py | OK |
| 00 | EventLog append-only | events property read-only | kernel/world/events.py | OK |
| 00 | WorldState derivable | replay() + apply() puros | kernel/world/replay.py | OK |
| 00 | DEFAULT_VOCAB inmutable | FrozenSet (AUD-08) | kernel/ontology/vocabulary.py | OK |

## Conectores y tools (fuera de alcance hasta C7)

| Spec | Concepto | Codigo actual | Ubicacion correcta | Estado |
|---|---|---|---|---|
| 06 | APITool | No existe | execution/tools/api_tools/ | FALTA |
| 06 | MCPTool | No existe | execution/tools/mcp_adapter.py | FALTA |
| 06 | FileTool | No existe | execution/tools/filesystem_tool.py | FALTA |
| 06 | DBTool | No existe | execution/tools/database_tool.py | FALTA |
| 06 | Tool base con description/schemas/requires_approval | base.py minimo | execution/tools/base.py | FALTA |
| 06 | 44 conectores | connectors/providers/ (stub) | Congelado hasta C7 | OK (fuera alcance) |
| 06 | ConnectorBridge | execution/tools/connector_bridge.py | OK | OK |

## Como se mantiene esta matriz

1. En C0.1 se revisa entera contra el codigo actual y se marcan estados.
2. En cada ciclo Cx, las filas afectadas cambian de estado (FALTA -> OK).
3. Si aparece una fila nueva, se anade con estado inicial FALTA o HUECO_SPEC.
4. Si dos filas entran en conflicto, gana la Spec Contradiction Rule:
   se abre decision en DECISIONS.md, se actualiza spec, se actualiza matriz.

