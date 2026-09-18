# KERNEL INVARIANTS - Audit cerrado

> Los 22 findings originales estan resueltos. El documento completo se
> conserva en docs/audits/archive/KERNEL_INVARIANTS_2026-09-18_cerrado.md
> como referencia historica.
>
> Estado actual del kernel: ver docs/STATUS.md.
> Plan de subida a spec: ver docs/SPEC_UPGRADE_PLAN.md.

## Resumen de resoluciones

| AUD | Resolucion |
|---|---|
| 01 | Fix: tenant_resolver inyectable en PolicyEngine |
| 02 | Fix: policies_dir inyectable; sin CWD-dependencia |
| 03 | Fix: validacion de tenant_id en _load_policy |
| 04 | Fix: applier.apply() fail-closed ante CRUD no manejado |
| 05 | Decision: event_type/data legacy documentado |
| 06 | Fix: 7 kinds anadidos a EVENT_VOCAB |
| 07 | Fix: EventLog.events property read-only (tupla) |
| 08 | Fix: Vocabulary con FrozenSet |
| 09 | Decision: OntologyBundle es design-time |
| 10 | Decision: ENTITY_TYPE_REGISTRY es global del proceso |
| 11 | Fix: DEV_ALLOW_ALL pasa por el evaluador |
| 12 | Fix: precedencia por especificidad + namespaces |
| 13 | Fix: INVARIANT_APPROVAL_SEGMENTS ampliado (FINANCIAL/DESTRUCTIVE) |
| 14 | Fix: is_canonical_relation_kind unificado |
| 15 | Decision: Action/ExecutionResult coexisten con docstrings |
| 16 | Fix: execute_action deriva tenant del contexto |
| 17 | Fix: README sincronizado |
| 18 | Fix: tests/agent-notes/bugs/ documentado |
| 19 | Fix: scripts/audit.sh arreglado |
| 20 | Fix: README sincronizado |
| 21 | Fix: .gitignore ampliado |
| 22 | Decision: data/policies/*.json se queda versionado |

## Referencias

- Estado operativo: docs/STATUS.md
- Plan de subida a spec: docs/SPEC_UPGRADE_PLAN.md
- Changelog: CHANGELOG.md