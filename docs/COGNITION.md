# Cognición persistente por (tenant, agente)

## Modelo

Cada par `(tenant_id, agent_id)` tiene las **4 memorias** persistidas:

| Memoria | Fichero | Semántica | Retención |
|---|---|---|---|
| **Working** | `working.jsonl` | hot cache, capado a 200 | rotativa |
| **Episodic** | `episodic.jsonl` | eventos inmutables ("qué le ha pasado") | append-only |
| **Semantic** | `semantic.jsonl` | hechos por key (upsert) | persistente |
| **Procedural** | `procedural.jsonl` | skills/SOPs por nombre | persistente |

Layout:
```
data/tenants/{tenant_id}/agents/{agent_id}/memory/
├── working.jsonl
├── episodic.jsonl
├── semantic.jsonl
└── procedural.jsonl
```

## Uso

```python
from agentic_os.cognition.memory import CognitionRegistry
cog = CognitionRegistry().for_agent("acme", "daily_social")

cog.working_add("Analizando CSV de leads")
cog.episodic_append("pipeline_started", {"pipeline": "leads_to_draft"})
cog.semantic_upsert("empresa.cliente", "ACME", confidence=0.95)
cog.procedural_register("inbox_zero", steps=[{"tool": "gmail_read", "order": 1}])
ctx = cog.context(query="ACME", k=5)
```

## Aislamiento

`tenant_id` y `agent_id` **se validan contra regex**
(`^[a-z0-9][a-z0-9_-]{0,127}$`) antes de construir la ruta. Path traversal,
barras, mayúsculas y caracteres especiales → `CognitionStoreError`.

## API

```bash
GET /api/v1/agents/{agent_id}/cognition
Header: X-Tenant-Id: <slug>
```

## Wiring automático

`PipelineRunner` instrumenta cada pipeline: antes → `episodic_append("pipeline_started")`,
éxito → `episodic_append("pipeline_completed")`, fallo → `episodic_append("pipeline_failed")`.

## Pendiente (roadmap)

- Rotación de `episodic.jsonl` por fecha.
- Migración a Postgres para tenants grandes.
- Compresión semántica: job que suma episódicos antiguos en hechos.
- Consolidación working → semantic por reglas deterministas.