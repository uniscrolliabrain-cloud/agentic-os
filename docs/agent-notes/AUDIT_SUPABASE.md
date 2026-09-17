# Informe de Audiencia - Agentic OS Kilo
Fecha: 2026-09-13
Rama: agent/kilo/bor-agencia (mergeado a master)

---

## PARTE 1: Connector + Persistence

### BUGS - `src/agentic_os/connectors/providers/supabase.py`

| # | Linea | Severidad | Descripcion |
|---|-------|-----------|-------------|
| 1 | 191 | **MED** | `storage.file.upload`: si `file_obj` es None (no se pasa en params), crash en `upload()`. Falta validacion: `if file_obj is None: raise ValueError("file es obligatorio")` |
| 2 | 213 | **LOW** | `storage.bucket.list` usa `storage.list_buckets()` - correcto, pero sin manejo de errores si Supabase no esta disponible |
| 3 | 223, 228 | **LOW** | `storage.folder.list` y `storage.file.list` son identicos (mismo codigo). Deberian unificarse o `folder.list` deberia usar `prefix` con slash |
| 4 | 269 | **MED** | `db.query` devuelve error con mensaje "Usa db.record.read con filtros" - contradice las capabilities listadas. `db.query` esta en capabilities pero no implementado como SQL directo |
| 5 | 301 | **MED** | `db.schema.inspect` retorna `ok=True` con `tables: []` en el except - engañoso. Deberia retornar `ok=False` o incluir `error` en output |

### BUGS - `src/agentic_os/infrastructure/persistence/supabase.py`

| # | Linea | Severidad | Descripcion |
|---|-------|-----------|-------------|
| 6 | 44 | **LOW** | El `try/except` en `_get_client` captura TODAS las excepciones silenciosamente. Si Supabase devuelve un error 401, se degrada a JSONL sin log de error visible (solo debug) |
| 7 | 103-107 | **MED** | `list_for_tenant` y `list_all` usan `mock_table.select.return_value.eq.return_value.order.return_value.execute` - si el mock cambia de configuracion entre llamadas, los tests fallan |

---

## PARTE 2: Auth + API + Config

### BUGS - `src/agentic_os/infrastructure/auth/jwt_verifier.py`

| # | Linea | Severidad | Descripcion |
|---|-------|-----------|-------------|
| 8 | 30 | **ALTO** | `payload.get("user_metadata", {}).get("tenant_id")` - si `user_metadata` es string o None, AttributeError. Falta: `if isinstance(payload.get("user_metadata"), dict)` |
| 9 | 27 | **MED** | `algorithms=["RS256", "ES256"]` - mezcla RSA y ECDSA. PyJWT selecciona segun la clave pero es confuso. Mejor detectar algoritmo de la clave |
| 10 | 28 | **MED** | `verify_aud: False` deshabilita verificacion de audience. Tokens de otros proyectos podrian ser aceptados |
| 11 | 46-52 | **MED** | Si `SUPABASE_URL` esta en `.env` como string vacio, `os.getenv` devuelve `""` (falsy) y cae a `settings.supabase_url`. Pero si settings esta mal configurado, RuntimeError no capturado |

### BUGS - `src/agentic_os/interfaces/api/rest.py`

| # | Linea | Severidad | Descripcion |
|---|-------|-----------|-------------|
| 12 | 94 | **ALTO** | `_verify_supabase_jwt` retorna None en exception. Si JWT es invalido/expirado, cae silenciosamente en auth legacy X-Tenant-Id. Deberia retornar explcitamente error o al menos loguear |
| 13 | 86-95 | **MED** | Sin timeout en verificacion JWKS. Si Supabase JWKS endpoint no responde, la request se cuelga indefinidamente |
| 14 | 104-116 | **LOW** | `x_admin_key` header aceptado en signature de `tenant_scope` pero nunca usado. Parametro muerto |
| 15 | 130 | **MED** | Si JWT valido tiene tenant_id desconocido en registry, retorna `str(tenant_id)` (ej: "tenant-x") en vez de "system". Esto permite acceso con scope no registrado |

### BUGS - `src/agentic_os/infrastructure/config/settings.py`

| # | Linea | Severidad | Descripcion |
|---|-------|-----------|-------------|
| 16 | 107 | **LOW** | `model_post_init` solo valida CREDENTIAL_ENCRYPTION_KEY en production. No valida que SUPABASE_URL+KEY esten configurados si EVENTLOG_IMPL=supabase |
| 17 | 115-119 | **LOW** | `__repr__` usa `model_dump()` que puede resolver lazy fields y exponer datos sensibles antes del redaction en ciertos flujos de serializacion |

---

## PARTE 3: Tests + CI + Configs

### BUGS - `pyproject.toml`

| # | Linea | Severidad | Descripcion |
|---|-------|-----------|-------------|
| 18 | **7-18** | **CRIT** | `supabase>=2.0.0` y `psycopg[binary]>=3.1.0` estan en `requirements.txt` PERO NO en `dependencies` de pyproject.toml. CI ejecuta `pip install -e ".[dev]"` que instala dev deps pero NO las runtime deps de Supabase. CI fallara con `ModuleNotFoundError: No module named 'supabase'` |

### BUGS - `.github/workflows/ci.yml`

| # | Linea | Severidad | Descripcion |
|---|-------|-----------|-------------|
| 19 | 5-7 | **CRIT** | CI triggers en `branches: [main]` pero la rama por defecto es `master`. CI nunca se ejecuta en pushes ni PRs a master |

### BUGS - `CONTRIBUTING.md`

| # | Linea | Severidad | Descripcion |
|---|-------|-----------|-------------|
| 20 | 12 | **MED** | Dice `cd uniscrolliabrain-cloud-agentic-os` pero el repo se llama `agentic-os-kilo` |
| 21 | 19 | **MED** | Dice "Crea una rama desde `main`" pero la rama base es `master` |

### BUGS - Tests

| # | Linea | Severidad | Descripcion |
|---|-------|-----------|-------------|
| 22 | test_supabase.py:71 | **LOW** | `test_storage_upload` usa `type(mock_storage).from_ = MagicMock()` pero el connector usa `getattr(storage, "from")`. Son atributos distintos en MagicMock. El test pasa por accidente |
| 23 | test_supabase.py:142 | **LOW** | `test_db_record_delete` - retorna `ok=True` pero no verifica `result.output["deleted"]`. Si el mock cambia, el test pasa igual |
| 24 | test_supabase.py | **MED** | Tests extensivos de connector usan MagicMock sin assertions significativas. Solo verifican `ok is True`. No prueban flujos de error |

---

## RESUMEN

**Total:** 24 hallazgos
- **CRIT:** 2 (pyproject.toml deps faltantes, CI branch wrong)
- **ALTO:** 2 (JWT user_metadata type check, JWT invalid fallthrough)
- **MED:** 11
- **LOW:** 9

**Antes de merge completo en main, arreglar:**
1. Aadir `supabase` y `psycopg[binary]` a `pyproject.toml` `dependencies`
2. Cambiar `branches: [main]` a `branches: [master]` en `ci.yml`
3. Arreglar `jwt_verifier.py` type check en `user_metadata`
4. Arreglar `rest.py` para que JWT invalido no caiga silenciosamente en auth legacy
