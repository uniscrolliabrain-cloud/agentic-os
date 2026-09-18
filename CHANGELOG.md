# Changelog

Todos los cambios notables de este proyecto se documentan en este archivo.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/),
y este proyecto usa [Semantic Versioning](https://semver.org/lang/es/).

## [Unreleased] — 2026-09-18

### Fixed

- AUD-01: kernel no importa `infrastructure.tenancy`. `PolicyEngine` con `tenant_resolver` inyectable.
- AUD-02: `PolicyEngine` con `policies_dir` inyectable. Sin dependencia del CWD.
- AUD-03: `_load_policy` valida `tenant_id` con `is_canonical_kind` (path traversal cerrado).
- AUD-04: `apply()` fail-closed. `entity_deleted` manejado explícitamente; kinds CRUD no reconocidos lanzan `InvalidEntityEventError`.
- AUD-07: `EventLog.events` es property read-only (tupla). Antes lista mutable pública.
- AUD-08: `Vocabulary` con `FrozenSet`. `DEFAULT_VOCAB` inmutable en runtime.
- AUD-11: `DEV_ALLOW_ALL` ya no retorna `allow` antes del evaluador.
- AUD-12: `PolicyEvaluator` con precedencia por especificidad (exacto > namespace > wildcard) y `deny` dentro del mismo nivel.
- AUD-13: `INVARIANT_APPROVAL_SEGMENTS` ampliado con FINANCIAL/DESTRUCTIVE (`refund`, `payment`, `finance.`, `stripe.`, `billing.`).
- AUD-14: una sola definición de slug canónico. `relations.py` usa `is_canonical_relation_kind` de `vocabulary.py`.
- AUD-16: `Executor.execute_action` deriva tenant del contexto, no fuerza `system`.
- AUD-19: `scripts/audit.sh` usa `kernel.world.events` (módulo real).

### Added

- `/api/v1/approvals/pending` y `/api/v1/approvals/{id}/decision` (spec 14).
- `/api/v1/missions` y `/api/v1/missions/{correlation_id}/trace` (spec 17).
- `docs/STATUS.md`: fuente de verdad operativa (spec vs implementado).
- `docs/AGENT_HANDOFF.md`: método de trabajo entre humano y agentes.
- `tests/kernel/test_no_kernel_imports_domains.py` robusto a imports relativos.

### Documented (decisiones tomadas)

- AUD-05: `event_type`/`data` marcado como legacy sin productor.
- AUD-09: `OntologyBundle` como artefacto de design-time, no guard de runtime.
- AUD-10: `ENTITY_TYPE_REGISTRY` global del proceso (no scoped por tenant).
- AUD-15: `Action`/`ExecutionResult` duplicados coexisten con docstrings claros.
- GAPs de `OBSERVABILITY.md` y `PERMISSIONS.md`: resueltos, marcas de RESUELTO.
- `docs/spec/*.md`: 16 ficheros NO vinculantes marcados `status: diseno (aspiracional)`.

### Tests

- `tests/conftest.py`: `collect_ignore_glob = ['manual/*']` excluye scripts manuales que rompían la captura de pytest en Windows.
- `tests/agent-notes/bugs/` y `automation/`: cálculo de raíz de repo corregido (`parents[3]`). Tests stale actualizados.
- Estado: 540 tests pasando.


## [0.1.0] - 2026-XX-XX

### Added
- Kernel determinista inicial (world, policy, ontology, types).
- Capa de cognición (beliefs, reasoning, planning, memory, skills, roles).
- Connector Kernel con 44 providers declarados (stub).
- API FastAPI + frontend React/Tailwind.
- Suite de tests con cobertura de bugs conocidos (`tests/bugs/`).
