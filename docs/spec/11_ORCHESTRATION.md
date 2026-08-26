# 11 — Orquestación

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