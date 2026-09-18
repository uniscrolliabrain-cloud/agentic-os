# 19 — Composición de agentes

> **status:** diseno (aspiracional). Este fichero describe un diseno
> objetivo; no todas sus partes estan implementadas. Ver `docs/STATUS.md`.


Cómo los miniagentes se conectan para resolver misiones complejas. La composición es **explícita** (declarada), nunca inferida.

## Regla de oro

Un agente solo puede ser invocado si su id aparece en el **`HANDOFF`** de otro. Esto hace que la composición sea un **grafo conocido y auditable**, no una invención del LLM.

## Modelo de handoff

```python
class Handoff(BaseModel):
    model_config = ConfigDict(frozen=True)
    to_agent_id: str
    payload_ref: str        # qué campo del context le paso
    condition?: str         # si_condición opcional
```

- `to_agent_id` debe existir en `10_AGENT_CATALOG.md`.
- `payload_ref` apunta a un output previo (del `MissionMemory.context`).
- Un handoff puede tener condición (solo se activa si se cumple).

## Ejemplos de composición

```
"Consigue 100 leads SaaS españoles, clasifícalos, súbelos al CRM y prepárame outreach"
  ↓
LEAD_GENERATION_AGENT
  → LEAD_GENERATION_AGENT.handoff RESEARCH_AGENT? no: LEAD_GENERATION (research+enrich+score)
  → LEAD_GENERATION_AGENT.handoff → CRM_AGENT (crear leads)
  → LEAD_GENERATION_AGENT.handoff → CONTENT_AGENT (outreach borrador)
  → CONTENT_AGENT.handoff → QA (validación) + COMMUNICATION_AGENT (tras aprobación)
```

## DAG dinámico

- El orquestador ensambla un `TaskPlan` cuyos `depends_on` respetan los handoffs declarados.
- Los nodos con `depends_on=[]` arrancan primero; el resto en cuanto sus deps terminan.
- Un `Cycle` en el DAG está **prohibido** (validación estructural del plan).

## Reglas

1. `handoffs` de cada agente son el ÚNICO vector de composición.
2. `dependencies` deben resolverse a agentes existentes.
3. Un agente solo lee inputs que sus `preconditions`/`dependencies` le garantizan.
4. El LLM nunca "decide" conectar dos agentes ad-hoc: propone un plan; la composición valida que el (des) DAG es legítimo según handoffs.


---

# Contratos ejecutables C0.4

> PENDIENTE DE REVISION HUMANA. Cierra el HUECO_SPEC de spec 19:
> schema de Handoff y motor de composicion.

## Schema Handoff (cognition/agents/schemas.py)

```python
class Handoff(_Frozen):
    from_agent_id: str
    to_agent_id: str
    payload_ref: str         # nombre del output del agente origen
    condition: str = ""       # vacio -> sin condicion
    description: str = ""
```

Reglas:
- `to_agent_id` debe existir en el catalogo (catalog.agent(id)).
- `payload_ref` apunta a un campo del output del agente origen,
  declarado en su `output_schema`.
- `condition` es una expresion determinista (sin LLM).
- Handoff es frozen + extra=forbid.

## Firma resolve_handoffs

```python
def resolve_handoffs(
    plan: TaskPlan,
    catalog: Catalog,
) -> TaskPlan:
    """
    Expande un TaskPlan sustituyendo los nodos-agente por la cadena
    de handoffs declarados. Devuelve un TaskPlan nuevo con:
    - depends_on inyectadas segun handoff.from -> handoff.to.
    - Nodos adicionales si el handoff crea una cadena nueva.

    Precondiciones:
    - Todos los agent_id del plan existen en catalog.
    - Todos los handoffs referencian agentes existentes.

    Postcondiciones:
    - El plan resultante es un DAG valido.
    - Si algun handoff no se puede resolver: ValidationError.
    """
    ...
```

## Verificacion de composicion

En C4c se verifica bidireccionalmente:

```python
for agent in catalog.list_agents():
    for h in agent.handoffs:
        target = catalog.agent(h)
        assert target is not None, f"{agent.id} -> {h} no existe"
```

Si algun handoff apunta a un agente inexistente: falla en load,
no en runtime.

## Que NO puede hacer el LLM (reafirmado)

- No emite Handoff directo.
- No conecta agentes ad-hoc.
- No modifica el plan tras construirlo.
- El LLM solo propone Intent; el resto es determinista.

## Handoffs por agente (del catalogo spec 10)

| Agente | Handoffs declarados |
|---|---|
| WEB_RESEARCH_AGENT | (a definir en C4b) |
| LEAD_GENERATION_AGENT | WEB_RESEARCH_AGENT, COMMUNICATION_AGENT |
| COMMUNICATION_AGENT | (a definir en C4b) |
| DATA_ANALYSIS_AGENT | COMMUNICATION_AGENT |
| CONTENT_AGENT | COMMUNICATION_AGENT |

Los "(a definir en C4b)" se completan al implementar los 5 agentes
con MiniAgentSchema valido. C4c verifica que cada handoff declarado
existe en el catalogo.
