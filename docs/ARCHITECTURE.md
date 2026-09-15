# Arquitectura

## Ley

**Kernel = invariantes. LLM propone, sistema dispone.**

Tres capas con contrato explícito:

```
INTERFACES      (HTTP, MCP, LLM)         ← habla con humanos / sistemas
    │
ORCHESTRATION   (loops, pipelines, VSM)  ← convierte intención en plan
    │
EXECUTION       (executor, tools)        ← ejecuta SOLO acciones aprobadas
    │
CONNECTORS      (CapabilityRegistry)     ← habla con el mundo real
    │
KERNEL          (world, policy, ontology, types)  ← NO TOCAR
```

## Flujo canónico de una acción

```
Usuario ─→ FrontAssistant (rápido)
        └→ Orchestrator (background)
              └→ LLM propone Intent (structured)
                    └→ PolicyEngine.decide(tenant, capability)
                          ├─ deny            → EventLog(ActionDenied)
                          ├─ require_approval → EventLog(ApprovalRequired)
                          └─ allow
                              └→ Executor.execute(action, params, tenant_id)
                                    └→ Tool/Connector
                                          └→ EventLog(ActionStarted, ToolCompleted)
```

## Capas y ficheros

- `kernel/`       → inmutable, versionado, invariantes ejecutables.
- `cognition/`    → beliefs, reasoning, planning, memory (4 tipos), agents.
- `execution/`    → `Executor`, tools deterministas, `ConnectorBridgeTool`.
- `connectors/`   → providers, 0 credenciales en código. Stub hasta `.env`.
- `orchestration/` → pipelines, scheduler, Temporal worker.
- `interfaces/`   → FastAPI (`rest.py`), MCP, LLM providers.
- `infrastructure/` → persistence (jsonl/postgres/supabase), tenancy, telemetry.

## Invariantes de arquitectura

1. El LLM nunca ejecuta nada: emite `Intent` (Pydantic).
2. Toda acción pasa por `PolicyEngine` antes del `Executor`.
3. `EventLog` es la fuente de verdad; `WorldState` es derivado por replay.
4. Un dominio extiende `DEFAULT_VOCAB`; nunca lo redefine.
5. Ninguna tool se ejecuta sin `tenant_id` en el contexto (fail-closed).

## Referencias

- Spec completa: `docs/spec/20_CLINE_IMPLEMENTATION_PROTOCOL.md`.
- Higiene y CI: ver `.github/workflows/ci.yml` + `Makefile`.
