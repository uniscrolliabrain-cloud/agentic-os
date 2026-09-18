# GOVERNANCE

**Policy governs Capability, not the agent.**

## Cadena de decisión

```
Intent              (LLM propone, estructurado con Pydantic)
   ↓
PolicyEngine.decide(tenant_id, capability, resource_kind, roles)
   ├─ "allow"            → Executor procede
   ├─ "deny"             → EventLog(ActionDenied); no ejecuta
   └─ "require_approval" → EventLog(ApprovalRequired); necesita humano
```

## Fuentes de política

| Fuente | Efecto | Alcance |
|---|---|---|
| `data/policies/{tenant_id}.json` | reglas explícitas (allow/deny/approve) | un tenant |
| `TenantConfig.enabled_capabilities` | gate de aislamiento | un tenant |
| `DEV_ALLOW_ALL=true` | allow-all solo en dev | global (bloqueado en prod) |
| Invariante del kernel | fuerza `require_approval` en `*.delete`/`*.publish` | global |

## Roles

Definidos en `cognition/roles/library.py`:
- `director` → puede `propose_intent`.
- `operator` → puede `execute`; `gmail_send` prohibido por defecto.
- `auditor`  → solo `read`; `forbidden_tools=["*"]`.

## Aprobación humana

- Todo `delete`, `publish`, `payment.*`, `email.send` → `require_approval`.
- El LLM **nunca** auto-aprueba.
- Cada decisión queda en `EventLog(Approved|Rejected)` con `actor_id` humano.

## Reglas de merge

- Cambios en `kernel/`, `policy/`, `connectors/` → **revisión obligatoria**.
- Tests de policy: `tests/agent-notes/bugs/test_bugNN_*.py`.