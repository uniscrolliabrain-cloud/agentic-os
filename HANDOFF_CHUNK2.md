# HANDOFF — CHUNK 2: Repo Hygiene + CI Verde

**Fecha**: 2026-09-14 16:30 UTC
**Branch**: `agent/kilo/bor-agencia`
**Tests**: ✅ 419 passed, 7 skipped, 0 failed
**Ruff**: ✅ 0 errores (en archivos modificados)
**Contexto del agente anterior**: Fixes de 24 bugs de AUDIT_SUPABASE.md + CHUNK 2 de higiene.

---

## ✅ COMPLETADO EN ESTA SESIÓN

### Bugs Supabase (24/24)
| # | Archivo | Fix |
|---|---|---|
| 1 | `connectors/providers/supabase.py:190` | `storage.file.upload`: validar `file_obj` no es None |
| 2 | `connectors/providers/supabase.py:212` | `storage.bucket.list`: try/except con logger.error |
| 3 | `connectors/providers/supabase.py:231` | `storage.folder.list`: prefix con trailing slash |
| 4 | `connectors/providers/supabase.py:278` | `db.query`: SQL directo via psycopg |
| 5 | `connectors/providers/supabase.py:365` | `db.schema.inspect`: ok=False en error |
| 6 | `infrastructure/persistence/supabase.py:47` | `_get_client`: logger.error + exc_info |
| 7 | `infrastructure/auth/jwt_verifier.py:30` | `user_metadata`: isinstance dict check |
| 8 | `jwt_verifier.py:27` | Detectar algoritmo desde `key_type` |
| 9 | `jwt_verifier.py:28` | `verify_aud=True` + SUPABASE_JWT_AUD opcional |
| 10 | `jwt_verifier.py:53` | `SUPABASE_URL.strip()` + fallback robusto |
| 11 | `interfaces/api/rest.py:95` | JWT invalid → HTTP 401 (no silent fallthrough) |
| 12 | `jwt_verifier.py:21` | `PyJWKClient(timeout=10)` |
| 13 | `rest.py:146` | `x_admin_key` usado antes del `if not x_tenant_id` |
| 14 | `rest.py:137` | tenant_id no registrado → `_DEFAULT_SCOPE` |
| 15 | `settings.py:107` | Validar supabase_url+key en model_post_init |
| 16 | `settings.py:122` | `__repr__` usa model_fields + getattr (safe) |
| 17 | `pyproject.toml:17` | Añadido `supabase>=2.0.0` + `psycopg[binary]>=3.1.0` |
| 18 | `.github/workflows/ci.yml:5` | `branches: [master]` |
| 19 | `CONTRIBUTING.md:12,19,30` | Nombre repo + rama base `master` |
| 20 | `tests/connectors/test_supabase.py:68` | Mock `from_` en instancia (getattr) |
| 21 | `tests/connectors/test_supabase.py:163` | `assert result.output["deleted"] == 1` |
| 22 | `tests/connectors/test_supabase.py:200` | Tests de error-path (4 nuevos) |
| 23 | `tests/infrastructure/test_supabase.py:64` | Helper `_make_list_chain_mock` robusto |
| 24 | `tests/infrastructure/test_supabase.py:95` | `test_list_all` implementado |

### Pipeline Runner (fix crítico — tests)
- **`runner.py`**: `run()` ahora acepta `(pipeline_id, tenant_id, params, ...)` y despacha a `PIPELINES[pipeline_id]`
- **`runner.py`**: Añadido método `emit_event()` que el pipeline `leads_to_draft` necesita para emitir `entity_created`
- **`test_pipeline_execution_invariants.py`**: Import explícito de `pipelines` para registro

### Repo Hygiene
- ✅ `requirements.txt` reescrito (antes tenía sintaxis Pyproject, rompía pip)
- ✅ Verificado `pip install --dry-run -r requirements.txt` — instala sin errors
- ✅ Mover `export`, `test_google_*.py` a `.scratch/` y `tests/manual/` (pending)
- ✅ Mover `archive/` → `docs/archive/` (pending)
- ✅ `data/tenants/registry.json` contiene api_keys de test (pending: sanitizar)

---

## ⏳ PENDIENTE (para nuevo chat implementar)

### Prioridad ALTA
1. **Repo hygiene scripts** (`scripts/cleanup_repo.sh`)
   - Mover `_*.py`, `_*.txt`, `export` → `.scratch/dev/`
   - Mover `archive/` → `docs/archive/`
   - Mover `test_google_*.py` → `tests/manual/`
   - Renombrar `Agent-Lock (1).py` → `agent_lock.py`, `Agent-Queue.py` → `agent_queue.py`
   - Eliminar `scripts/Executor.py` (duplicado)
   - Sanitizar `data/tenants/registry.json` → `registry.example.json`

2. **Docs vacíos** — reescribir con contenido real:
   - `docs/ARCHITECTURE.md` (40 bytes → ~60 líneas)
   - `docs/INVARIANTS.md` (38 bytes → ~45 líneas)
   - `docs/ONTOLOGY.md` (35 bytes → ~35 líneas)
   - `docs/GOVERNANCE.md` (39 bytes → ~30 líneas)
   - `docs/COGNITION.md` (crear — cierra CHUNK 1)

3. **Scripts** (`scripts/audit.sh`, `scripts/diag_pipelines.py`, `scripts/diagnose.sh`)

4. **Makefile** (raíz)

5. **`.gitignore`** — añadir `.scratch/`, `data/tenants/*.json`, `.credentials/`, etc.

6. **`data/tenants/README.md`** — documentar runtime state

### Prioridad MEDIA
7. **`tests/domains/conftest.py`** — fixture autouse para aislar `ENTITY_TYPE_REGISTRY`
   - Aunque los tests pasan ahora, son frágiles por orden de ejecución
   - Snapshot/restore del registry entre tests

8. **Warnings de tests** — `@pytest.mark.asyncio` en tests no-async en `test_supabase_jwt_auth.py`

### Prioridad BAJA
9. **mypy** — 235 errores pre-existentes (no son del CHUNK 2)
10. **`settings.py:125` deprecation** — `self.model_fields` → `type(self).model_fields`

---

## Comandos para validar (nuevo chat)

```bash
cd "C:\Users\Alfonso\Desktop\git hub repos\agentic-os-kilo"

# Tests
pytest -q --tb=short                    # objetivo: 419 passed, 0 failed

# Lint
ruff check .                            # 0 errores en archivos modificados

# requirements.txt
pip install --dry-run -r requirements.txt  # sin SyntaxError

# Git
git status --short                     # ver cambios
git diff --stat                        # 10 archivos modificados
```

---

## Cambios de comportamiento (breaking)

| Cambio | Archivo | Impacto |
|---|---|---|
| JWT inválido → 401 | `rest.py` | Fallos silenciosos ahora rechazados. Fail-closed. |
| `db.query` usa psycopg | `supabase.py` | Requiere DSN en credentials/config o settings |
| `verify_aud=True` | `jwt_verifier.py` | Requiere `aud` en JWT; configurar `SUPABASE_JWT_AUD` si falla |
| `x_admin_key` funciona sin tenant_id | `rest.py` | Admin bypass retorna "system" sin X-Tenant-Id |
| `tenant_scope` retorna tupla | `rest.py` | Tests de JWT auth actualizados |
| `run(pipeline_id, ...)` | `runner.py` | Firma cambiada: `(pipeline_id, tenant_id, params)` |
| `emit_event` en runner | `runner.py` | Nuevo método para pipelines que emiten eventos |