# 15 — Estado y memoria

Cómo el sistema recuerda el estado de cada misión y usa el historial.

## Fuente de verdad

- **EventLog** (`kernel/world/events.py`) es la fuente de verdad y es **inmutable**.
- El **estado derivado** se obtiene por **replay** (`kernel/world/replay.py`).
- No se muta estado: se aplica un evento y se proyecta.

## Memoria por misión

Cada misión (`TaskPlan`) tiene un **contexto** que acumula el output de sus nodos:

```python
class MissionMemory(BaseModel):
    plan_id: str
    tenant_id: Optional[str]
    context: dict = Field(default_factory=dict)   # node_id → output
    facts: list[Fact] = Field(default_factory=list)
    history: list[EventRef] = Field(default_factory=list)
```

- `context` guarda la salida de cada microacción (para handoffs).
- `facts` son afirmaciones validadas a lo largo de la misión (no invenciones).
- `history` apunta a los eventos del EventLog (trazable).

## Memoria a largo plazo

- `cognition/memory/` ya distingue episódica / semántica / procedural / working.
- Para el sistema de miniagentes, `procedural` = el catálogo de skills/pipelines (estable).
- `episodic` = misiones previas (para "como la última vez").

## Reglas

1. Nada entra en `context`/`facts` sin pasar por su schema.
2. Un nodo SOLO lee: `context` de sus dependencias + sus preconditions.
3. Los `facts` van precedidos por una fuente (las fuentes dan verosimilitud en QA).
4. El estado de un agente entre misiones se persiste en el tenant (`data/tenants/<slug>/`).