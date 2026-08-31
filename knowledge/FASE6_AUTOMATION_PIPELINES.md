# FASE 6 — Automation & Content Pipeline

Estado: **implementada**, con providers SIMULADOS (ninguna API real conectada aún).

## Qué aporta

El OS ahora puede **programar trabajo por tenant** y ejecutar pipelines de contenido:

| Pipeline | Qué hace | Tools | Salida |
|---|---|---|---|
| `daily_social` | Saca contenido de la cache local de Drive (`content_to_post/{tenant}`), genera copy (Gemini si hay key, si no plantilla), **publica en Meta (SIMULADO)** | `drive_list_files`, `drive_read_file`, `meta_post_publish` | artefacto en `data/tenants/{tenant}/artifacts/{date}/` |
| `leads_to_draft` | Lee leads (CSV/JSON) de `leads/{tenant}`, personaliza un email por lead y deja **borradores** (nunca envía) | `drive_list_files`, `drive_read_file`, `gmail_create_draft` | drafts en `data/tenants/{tenant}/drafts/` |
| `inbox_watcher` | Lista unread (simulado), clasifica (lead/soporte/spam) con LLM y genera respuesta **en borrador** para leads | `gmail_list_unread`, `gmail_create_draft` | drafts + evento `InboxProcessed` |

## Scheduler real (APScheduler)

- `src/agentic_os/orchestration/scheduler.py` — `Scheduler` con `schedule_daily`, `schedule_interval`, `list_schedules`, `remove_schedule`.
- Persistencia **por tenant**: `data/tenants/{tenant_id}/schedules.json` (sin Redis). Cada tenant solo ve/edita los suyos.
- Al disparar: emite `ScheduledPipelineStarted` y llama a `orchestrator.handle_pipeline(pipeline_id, tenant_id)`.
- Resta: `Scheduler` se crea con `on_trigger` en `rest.py`.

## API nueva (todas filtradas por el tenant de la cabecera `X-Tenant-Id`)

- `GET /api/schedules` · `POST /api/schedules` · `DELETE /api/schedules/{id}`
- `GET /api/drafts` — borradores del tenant
- `GET /api/artifacts` — lista de artefactos del tenant
- `GET /api/artifacts/{tenant_id}/{artifact_id}` — valida que `tenant_id == scope` (FASE 4)

## Tools nuevas (registradas en `build_default_registry`)

- `meta_post_publish`, `meta_carousel_publish` → **SIMULADAS** (validan page_id/message/image_url; nunca llaman a graph.facebook.com). Preparadas para la fase real con `META_PAGE_ID`/`META_PAGE_ACCESS_TOKEN` en `.env`.
- `drive_list_files`, `drive_read_file`, `drive_search` → cache local `data/tenants/{tenant}/drive/` (credenciales Google reales de momento no requeridas).
- `gmail_create_draft` → deja JSON en `data/tenants/{tenant}/drafts/` (no envía).
- `gmail_list_unread` → simulado para el watcher.
- `scheduler_create_job`, `scheduler_list_jobs`, `scheduler_delete_job` → requieren la instancia `Scheduler` (inyectada por `rest.py`).

## Frontend

Tabs por tenant en `App.jsx`: **Chat · Briefings · Hoy · Calendario · Drafts**, todas usando `headersWithTenant()`.

## Contratos respetados

- Tools **nunca** devuelven dict con clave `error` → `ToolValidationError`.
- Aislamiento estricto por tenant: `data/tenants/{tenant_id}` nunca se cruza con otro.
- Meta es `SIMULATED` con `real_execution: false`; el borrador nunca se envía sin aprobación humana (invariante de FASE 5).

## Para pasar a producción (cuando se conecten APIs reales)

1. `.env`: `META_PAGE_ID`, `META_PAGE_ACCESS_TOKEN` (Meta), `GOOGLE_*` (Drive/Gmail) — hasta entonces la cache local y los drafts SIMULADOS cubren el flujo.
2. Sustituir los bodies de `meta_tool.py` y `gmail_tool.py` por los adapters reales del Connector Kernel (mismo camino canónico `capability → connector → resultado normalizado`).
3. `google-api-python-client` para Drive real (hoy no está en `requirements.txt` porque no se usa).