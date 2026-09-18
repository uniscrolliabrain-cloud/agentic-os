# 11 — Orquestación

> **status:** diseno (aspiracional). Este fichero describe un diseno
> objetivo; no todas sus partes estan implementadas. Ver `docs/STATUS.md`.


Capa que convierte la **intención humana** en un **plan ejecutable** (TaskGraph/DAG)
y despacha cada nodo al miniagente correspondiente.

## Capas

```
1. INTENT LAYER      → qué quiere conseguir el usuario ("lanzar una campaña")
2. PLANNING LAYER    → intent → plan → grafo de tareas (TaskGraph)
3. EXECUTION LAYER   → cada nodo lo ejecuta su miniagente (pipeline/SOP + tools/APIs)
```

## Orquestador (back office)

- El usuario habla con **Laia** (PR). El orquestador recibe el mensaje **en segundo plano** (ver README "dos velocidades").
- El orquestador NUNCA bloquea la respuesta al usuario.

### Router determinista (camino rápido)

1. Se normaliza el mensaje (intención → tokens canónicos).
2. Se busca en un **mapa intención→(miniagente, contrato)** de patrones frecuentes.
3. Si hay match determinista → se instancia el `TaskPlan` directamente (sin LLM).

### Intérprete LLM (camino de razonamiento)

- Solo se usa si el router no encuentra match.
- El LLM genera una **`Intent` estructurada** con `kind=<miniagente>`, `entity_id`, `payload`.
- El sistema construye el `TaskPlan` y lo valida; el LLM **nunca ejecuta**.

## TaskGraph / DAG

- `TaskPlan` (misión) → lista de `TaskNode` con `depends_on` (DAG).
- El scheduler ejecuta nodos cuyas dependencias estén `COMPLETED`.
- Cada nodo delega en un miniagente (`TaskNode.agent_id`).

## Priorización

1. Nodos raíz (sin deps) primero, en paralelo si las tools lo permiten.
2. Los nodos de mayor importancia para la misión se despachan antes.
3. Los nodos con `human_approval=true` se pausan en `NEEDS_APPROVAL` (ver 14).

## Pendientes

- Si un nodo falla y su pipeline define `error_recovery` → se aplica.
- Si no → el nodo pasa a `FAILED`; los dependientes pasan a `BLOCKED`.
- El plan no muere: se notifica al usuario y se espera decisión (reintentar / saltar / cancelar).

## Referencias
- Schemas: `07_PYDANTIC_CONTRACTS.md`
- Estados: `05_STATE_MACHINE.md`
- Planificación↔agentes: `19_AGENT_COMPOSITION.md`


---

# Contratos ejecutables C0.4

> PENDIENTE DE REVISION HUMANA. Cierra el HUECO_SPEC de spec 11:
> firmas, serializacion y validacion de TaskPlan.

## Firma de build_task_plan

```python
def build_task_plan(
    intent: Intent,
    catalog: Catalog,
) -> TaskPlan:
    """
    Construye un TaskPlan determinista a partir de un Intent.

    Precondiciones:
    - intent.kind resuelve a un agente del catalogo (catalog.agent).
    - El agente declara sus microacciones y sus handoffs.

    Postcondiciones:
    - TaskPlan.nodes es un DAG valido (sin ciclos, sin deps huerfanas).
    - Cada TaskNode.agent_id existe en catalog.
    - El plan es frozen (inmutable).

    Errores:
    - UnknownIntentError si intent.kind no resuelve.
    - InvalidPlanError si el DAG tiene ciclos o deps huerfanas.
    """
    ...
```

## Serializacion TaskPlan <-> JSON

TaskPlan es frozen + extra=forbid. Serializa con:

```python
plan_json = plan.model_dump_json()           # -> str
plan = TaskPlan.model_validate_json(plan_json)
```

En disco (para `MissionMemory`): `data/tenants/<tid>/missions/<plan_id>.json`.

## Validacion estructural

Al construir (TaskPlan.__init__ via field_validator en schemas.py):

1. node.id unicos.
2. Todo depends_on referencia a un node existente.
3. Sin ciclos (topological sort debe completar).
4. Al menos 1 node.

Si falla cualquiera: ValidationError, no se construye.

## Orden de ejecucion

```python
def run_plan(plan: TaskPlan, scheduler: TaskScheduler) -> MissionResult:
    """
    - Nodos con depends_on=[] arrancan primero (paralelo si el
      scheduler lo permite).
    - Nodo se despacha cuando todas sus deps estan COMPLETED.
    - Nodo con state=NEEDS_APPROVAL pausa el plan; el scheduler
      lo salta y espera decision humana.
    - Si un nodo FAILED: dependientes -> BLOCKED. Plan no muere,
      espera decision (reintentar/saltar/cancelar).
    - Plan COMPLETED cuando todos los nodos terminales estan
      COMPLETED o SKIPPED.
    """
    ...
```

## Quien puede crear un TaskPlan

- Solo `build_task_plan(intent, catalog)`.
- El LLM nunca emite TaskPlan directo (D09, D13, D14).
- El orquestador es el unico que llama a build_task_plan.
- Si el LLM devuelve un JSON con estructura tipo TaskPlan, se ignora.

## Eventos emitidos

| Evento | Cuando | Payload minimo |
|---|---|---|
| PlanCreated | build_task_plan exito | plan_id, mission, node_count |
| PlanStarted | antes del primer dispatch | plan_id, started_at |
| NodeDispatched | antes de cada ejecucion | plan_id, node_id, agent_id |
| NodeCompleted | al terminar OK | plan_id, node_id, output_keys |
| NodeFailed | al terminar KO | plan_id, node_id, error_state |
| NodeStateChanged | en cada transicion | plan_id, node_id, from, to |
| PlanPausedForApproval | nodo entra NEEDS_APPROVAL | plan_id, node_id |
| PlanResumed | tras aprobacion | plan_id, node_id, decision |
| PlanCompleted | todos terminales OK | plan_id, duration_ms |
| PlanFailed | algun terminal FAILED sin recovery | plan_id, error_state |

Todos llevan `tenant_id` + `correlation_id` + `command_id`.
