# INVARIANTS

Las invariantes están **implementadas** y **testeadas** en el kernel. No son comentarios.

## Kernel / World

**Ubicación**: `src/agentic_os/kernel/world/invariants.py`
**Tests**: `tests/kernel/test_invariants.py`, `tests/kernel/test_worldstate_typed.py`

- `Event immutable`      → `Event` es `KernelModel` (frozen).
- `Log append-only`      → `EventLog.append()` no modifica, solo añade.
- `State derivable`      → `replay(log)` reconstruye `WorldState` deterministamente.
- `apply pure`           → `apply()` no muta el estado original.
- `version +1 per event` → cada evento incrementa `state.version`.
- **CorruptEventError**  → si un evento es inválido, el replay falla con el índice; nunca devuelve estado parcial.

## Kernel / Policy

**Ubicación**: `src/agentic_os/kernel/policy/invariants.py`, `evaluator.py`
**Tests**: `tests/agent-notes/bugs/test_bug5_devallowall.py`, `tests/security/test_hardening_fase1.py`

- `Policy immutable`             → `Policy` y `PolicyRule` son frozen.
- `Deny by default`              → sin regla explícita, `deny`.
- `Approval != granted`          → `require_approval` no ejecuta.
- `Engine pure`                  → `decide()` no tiene side-effects.
- **Delete/Publish → approval**  → el `PolicyEvaluator` **fuerza** `require_approval` en `*.delete`/`*.publish`, incluso si una regla dice `allow`. Una regla puede endurecer; nunca suavizar.

## Kernel / Ontology

**Ubicación**: `src/agentic_os/kernel/ontology/invariants.py`, `validator.py`
**Tests**: `tests/kernel/test_ontology_*.py`

- `is_canonical_kind`  → slug en minúsculas con `.`, `_`, `-`.
- `DEFAULT_VOCAB` inmutable en runtime.
- Un dominio **extiende** con namespace propio (`clinic.patient`), nunca colisiona.
- `validate_against_metamodel` falla-closed ante: colisión, no canónico, refs rotas.

## Cómo probar que no has roto nada

```bash
pytest tests/kernel/ -q
```

También corre `pytest tests/agent-notes/bugs/ -q` — los 20 tests de regresión
documentan bugs reales encontrados y son parte del contrato de merge.

Cualquier fallo aquí **bloquea el merge** (ver `.github/CODEOWNERS`).