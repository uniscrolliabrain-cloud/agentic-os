# 19 — Composición de agentes

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