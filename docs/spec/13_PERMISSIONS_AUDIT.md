# Tenant & Policy AUDIT

> Hardning task. Traza de aislamiento multi-tenant y policy enforcement.

## 1. Fuente de verdad del tenant: `X-Tenant-Id` (FASE 4)

`rest.py` resuelve el tenant **siempre desde la cabecera** `tenant_scope` (dependencia), **nunca del body**.
- `/api/execute` (línea 527): `scope: str = Depends(tenant_scope)` → `tenant = _tenant_registry.get(scope)`. ✅
- `/api/chat`: `req: ChatRequest` incluye `tenant_id` en el body **pero** el endpoint usa `tenant_scope` como fuente, ignorando `req.tenant_id` (se asume para el histórico de conversación, que ya filtra por header). ⚠️ **necesario confirmar** si `req.tenant_id` puede ser sobreescrito maliciosamente.
- `_start_orchestration_task(message, conversation_id, tenant_id)` recibe `tenant_id` del scope. ✅

## 2. Policy engine (`kernel/policy/engine.py`)
Tres métodos de decision, **dos paths de decisión** → fuente de confusión:

| Método | Usa `tenant_id`? | Usa `is_allowed()` (enabled_capabilities)? | Observación |
|---|---|---|---|
| `can(capability, resource_kind, roles)` | ❌ (usa `self.tenant_id` del engine) | ❌ | Path global; no multi-tenant real |
| `is_allowed(tenant_id, action)` | ✅ | ✅ | **Filtra por enabled_capabilities → deny implícito** |
| `can_for_tenant(tenant_id, capability, ...)` | ✅ | ✅ | Igual que is_allowed pero devuelve `Decision` completa |

## 3. Dónde se aplica Policy (decision points reales)

| Capa | Archivo:Línea | ¿Chequea policy? | Comentario |
|---|---|---|---|
| **API** | `rest.py:532` | ✅ `_policy_engine.is_allowed(tenant, action)` antes de `/api/execute` | **Correcto, con fail-closed** |
| **Orchestrator** | `orchestrator.py:handle_user_message` | ❌ — solo propone Intent, no ejecuta | ✅ Diseño correcto (LLM propone) |
| **Executor.execute()** | `executor.py:87` | ⚠️ **INCONSISTENTE** — véase detalle abajo | ❗ GAP |
| **Scheduler → handle_pipeline** | `orchestrator.py:65` | ❌ | Pipeline disparado sin chequear policy |
| **PipelineRunner.run** | `runner.py` | ❌ | Llama a `executor.execute()` sin tenant context explícito |

### Gap crítico: Executor.execute()
```python
result = _executor.execute(
    action=action,
    params=req.params,
    context=TenantContext(tenant=tenant))     # ← tenant en context
```
- El `context.tenant.id` **sí llega** a `_policy_decision()` (línea 87, vía `_tenant_of(context)` → `tid`). ✅
- **Pero**: no se pasa `correlation_id` al `_audit()` → los eventos `ActionStarted/ToolCompleted` **no son trazables** a la Mission. ❌

### Gap crítico: Scheduler
`scheduler.py` llama `orchestrator.handle_pipeline(pipeline_id, tenant_id)` → este método no pasa `TenantContext` al ejecutar → si un pipeline llama a `gmail_send`, la política **no puede distinguir el tenant del disparador programado**. ⚠️

## 4. Aislamiento de datos por tenant (filesystem + registry)
| Recurso | Path | Filtrado por tenant? |
|---|---|---|
| Conversaciones | `data/tenants/{tenant_id}/conversations/` | ✅ (FASE 4) |
| Knowledge | `knowledge/_shared/` + `data/tenants/{tenant_id}/knowledge/` | ✅ |
| Artifacts | `data/tenants/{tenant_id}/artifacts/` | ✅ (FASE 6) |
| Drafts | `data/tenants/{tenant_id}/drafts/` | ✅ |
| Schedules | `data/tenants/{tenant_id}/schedules.json` | ✅ |
| EventLog | `data/tenants/{tenant_id}/events.jsonl` | ✅ (JsonlEventLog filtra) |
| Drive cache | `data/tenants/{tenant_id}/drive/` | ✅ |

## 5. Conclusión
- **Aislamiento de tenant en filesystem y API está implementado y verificado.**
- **`enabled_capabilities` funciona como gate de aislamiento** (tenant sin caps → deny). ✅
- **GAP 1:** `correlation_id` se pierde en el Executor — **no trazabilidad Mission→EventLog.**
- **GAP 2:** Scheduler no inyecta `TenantContext` en pipelines — **policy saltado en tareas programadas.**
- **GAP 3:** doble path de decisión (`can()` vs `can_for_tenant()`) → confusión de uso.
