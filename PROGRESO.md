# PROGRESO — Auditoría Real (61 puntos)

> Fuente única de verdad. Actualizar tras CADA punto con salida literal.
> Orden de bloques: A → F → E → D → B → C → G
> Reglas: protocolo de entrega en AUDITORIA_REAL_PENDIENTES.md; bugs del doc de referencia en PLAN_IMPLEMENTACION_CLINE_V2.md.

## BLOQUE A — Entidades de dominio tipadas (en curso)

- [x] A1 — DomainEntity base — `7 passed in 0.35s` — domain_models.py + tests/domains/test_domain_entity.py
- [x] A2 — Lead y Proposal — incluido en `18 passed in 0.37s` — domain_models.py
- [x] A3 — Brand y Campaign — incluido en `18 passed in 0.37s` — domain_models.py
- [x] A4 — BlogPost + CoachingClient, SessionNote, TherapyClient, Appointment — `18 passed in 0.37s`
- [x] A5 — ENTITY_TYPE_REGISTRY (9 tipos, fail-closed, integridad) — `35 passed in 1.93s` (tests/domains completos) — test_entity_registry.py — **SIGUIENTE: A6**
- [ ] A6 — WorldState tipado (Union + discriminador kind) — **requiere reescribir tests/bugs/test_bug8_pydantic_falso.py**
- [ ] A7 — Applier transaccional (world/applier.py)
- [ ] A8 — Replay sin corrupción silenciosa (world/replay.py)
- [ ] A9 — Migrar pipelines existentes a entidades tipadas
- [ ] A10 — Gate Bloque A (pytest kernel+domains + script manual Lead→Proposal→apply→replay)

## BLOQUE F — Agent Contracts (siguiente bloque tras A)

- [ ] F1 — Ampliar BaseAgent (capabilities, state tipado, on_failure)
- [ ] F2 — FailurePolicy (contrato Pydantic)
- [ ] F3-F5 — Migrar agentes existentes (rol "director" del Orchestrator)
- [ ] F6-F8 — Tests de política de fallos
- [ ] F9-F10 — Gate Bloque F

## BLOQUE E — Escritura atómica de credenciales (swap simple)

- [ ] E1 — SecureCredentialStore (ontology_prompt_finalv3.md líneas 2502-2640, copy tal cual) + fail-closed sin CREDENTIAL_ENCRYPTION_KEY

## BLOQUE D — Identidad y JWT

- [ ] D1 — Auditoría de tenancy actual (deps.py/rest.py)
- [ ] D2 — UserContext (Pydantic)
- [ ] D3 — UserRegistry (usuarios por tenant, NO duplicar TenantRegistry)
- [ ] D4 — JWT (pyjwt, tenant_id+roles firmados, Invariante 18)
- [ ] D5 — get_current_user() en PARALELO a tenant_scope (no romper tests/security)
- [ ] D6 — PolicyEngine: conectar UserContext.roles
- [ ] D7 — Destructive/public ops con require_approval (usar RiskClass existente)
- [ ] D8 — can_for_user()
- [ ] D9 — Test protección física del tenant
- [ ] D10 — Gate Bloque D (pytest tests/security/ -q completo)

## BLOQUE B — SMC / Crystallizer (tras C o en paralelo)

- [ ] B1 — IntentMatch (cognition/reasoning/intent_match.py)
- [ ] B2 — MatchmakingResult
- [ ] B3 — Clasificador determinista (sin LLM)
- [ ] B4 — Contratos de intención
- [ ] B5 — Crystallizer básico (usa Command de connectors/core/models.py)
- [ ] B6 — Crystallization Loop (LLM propone, nunca ejecuta — Inv. 12)
- [ ] B7 — SemanticCompiler completo
- [ ] B8 — Integración REST del SMC
- [ ] B9 — Tests determinismo + grep tool.run/connector.execute en cognition/ = 0
- [ ] B10 — Gate Bloque B

## BLOQUE C — Model Mesh

- [ ] C1 — Inventario de providers (Gemini, Groq, Mock)
- [ ] C2 — ModelRouter base
- [ ] C3 — Routing determinista
- [ ] C4 — RateLimiter aplicado al Mesh (reutilizar connectors/core/rate_limiter.py)
- [ ] C5 — Routing estructurado (response_schema uniforme)
- [ ] C6 — Inferencia concurrente
- [ ] C7 — Auditoría de routing en EventLog
- [ ] C8 — Failover real (RetryEngine + RateLimiter, auditado)
- [ ] C9 — Configuración segura (Settings/.env)
- [ ] C10 — Gate Bloque C

## BLOQUE G — Lint y auditoría estática real

- [ ] G1 — ruff select por tandas: I001 → UP035/UP006 → SIM102 → BLE001
- [ ] G2 — mypy src real, salida pegada
- [ ] G3-G10 — Cerrar errores (kernel/executor → connectors → cognition/orchestration)

## LOTES PLANIFICADOS (para agilizar)

- Lote 1: A5
- Lote 2: A6 + A8 (mismo subsistema state/replay, un run)
- Lote 3: A7 + A9
- Lote 4: A10 (gate)

## NOTAS

- Prompt 100/100 no existe en MASTER_PLAN.md (solo hay 99)
- HubSpot/Slack quedan en stub (decisión confirmada en plan V2)
- test_google_real.py pendiente de ejecución completa (timeout anterior)
- test_bugs: 78/78 pasando (verificado antes de Bloque A)
