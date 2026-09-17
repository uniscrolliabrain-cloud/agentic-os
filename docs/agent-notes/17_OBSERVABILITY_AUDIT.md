# EventLog AUDIT — Propagación real de eventos y correlation_id

> Hardning task. Este documento describe el estado ACTUAL de auditoría del EventLog
> (no una feature). Sirve para validar qué falta propagar antes de conectar providers reales.

## 1. Evento base actual (`kernel/world/events.py`)
`Event` ya soporta todo lo necesario → el bug NO está en el esquema, está en la **propagación**:

| Campo | Tipo | Status |
|---|---|---|
| `id` | str | ✅ se autogenera |
| `kind` | str | ✅ emitido |
| `entity_id` | str | ✅ |
| `payload` | dict | ✅ (resumido por `_params_summary`) |
| `at` | datetime | ✅ |
| `actor_id` | Optional[str] | ✅ |
| `tenant_id` | str (obligatorio) | ✅ |
| `correlation_id` | Optional[str] | ✅ **existe en el modelo pero casi nunca se propaga** |
| `command_id` | — | ❌ **NO existe en Event** (no está en el schema) |

### Gap crítico inmediato
`Event` NO tiene atributo `id` (de comando) → se cae de la trazabilidad Mission→EventLog. Hay dos opciones:
1. Añadir `command_id: Optional[str]` (o `mission_id`) a `Event` → touch `events.py` (kerno/bug fix, no feature).
2. Usar `correlation_id` como sustituto → **NO**, porque no siempre hay 1 comando = 1 correlación en pipelines programados.

## 2. Tabla de eventos emitidos hoy (propagación REAL)

| Emisor | Evento | `tenant_id` | `actor_id` | `correlation_id` | OK/BUG |
|---|---|---|---|---|---|
| Orchestrator.handle_user_message | IntentProposed | ✅ (param) | ✅ (role.name) | ❌ no se pasa | **BUG** |
| Orchestrator.handle_pipeline (pipeline desconocido) | ScheduledPipelineFailed | ✅ | ✅ "scheduler" | ❌ | **BUG** |
| PipelineRunner.run | PipelineStarted | ✅ | ❌ "pipeline_runner" hardcodeado | ✅ (param) | OK* |
| PipelineRunner.run | PipelineCompleted/Failed | ✅ | ❌ "pipeline_runner" | ✅ | OK* |
| Executor.execute | ActionStarted | ✅ | ✅ (param) | ❌ se ignora | **BUG** |
| Executor.execute | ToolCompleted/ToolFailed | ✅ | ✅ | ❌ | **BUG** |
| Executor.execute | ApprovalRequired/ActionDenied | ✅ | ✅ | ❌ | **BUG** |
| executor.execute_action (legacy Action) | (misma familia) | ❌ None → "system" | ✅ | ❌ | ⚠️ legacy |

\* `actor_id="pipeline_runner"` es estático → pérdida de quién disparó. Mínimo aceptable, pero ideal pasar `correlation_id` al actor.

## 3. Origen del `correlation_id`

### Chat path (`handle_chat` → `_start_orchestration_task` → `_run`)
- Línea 256: `task_id = f"task_{uuid4().hex[:8]}"` → **este `task_id` es el correlation_id natural** pero:
  - NO se pasa como `correlation_id` al `handle_user_message` (línea 268).
  - NO se pasa al `_executor.execute` en `_try_execute` (línea 245) ni a `handle_pipeline`.
  - Resulta: cada mensaje de chat arranca su propia correlación pero **se pierde en el primer salto**.

### Scheduler path
- `scheduler.py` genera un `run_id` pero **no se inyecta en `handle_pipeline`** → el pipeline arranca sin correlación con el job programado.

### Endpoint `/api/execute` directo
- Línea 535: `execute(action=..., params=...)` → **ni `tenant_id` ni `correlation_id` ni `actor_id` llegan explícitos** (el `tenant_id` se deduce del context, OK, pero no el resto).

## 4. Plan de reconsstrucción (post-este audit)

1. **Crear `command_id`** en `rest.py` al recibir el request → propagarlo como:
   - request_id en el background task
   - correlation_id en `handle_user_message`, `execute()`, `handle_pipeline`, `PipelineRunner.run()`, `_audit()`
2. **Executor._audit()** pasa `correlation_id` a `Event(correlation_id=...)`.
3. **Scheduler** pasa `run_id` como `correlation_id` a `handle_pipeline`.
4. **Actor_id de pipeline** → derivado del disparador (scheduler / human / api), no hardcodeado.

## 5. Conclusión
- El esquema `Event` ya soporta trazabilidad → no hay que tocar el modelo sino **propagar el id** en 5 puntos: `_start_orchestration_task`, `_try_execute`, `handle_user_message`, `handle_pipeline`, `Executor.execute/_audit`.
- `command_id` (como `mission_id`) debería añadirse a `Event` en una fase de hardening posterior (kerno bugfix), pues la trazabilidad Mission→EventLog queda rota sin él.
