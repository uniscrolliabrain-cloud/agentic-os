# 17 — Observabilidad

Todo lo que pasa es registrable y auditable. La interfaz de control y auditoría se alimenta del EventLog.

## Qué se observa

- Cada microacción ejecutada → `MicroActionStarted` / `MicroActionCompleted`.
- Cada fallo → `MicroActionFailed` (con `error_state`).
- Decisiones de policy → `IntentProposed`, `ActionDenied`, `Approved`, `Rejected`.
- Espías por evento → `MicroActionSkipped`, `PipelineEnded`, `MissionCompleted`.
- Handoff entre agentes → `AgentHandoff` (from, to, payload_ref).

## Trazabilidad

Cada evento lleva:
- `event.at` (UTC)
- `event.actor_id` (agente/nodo que lo emite)
- `event.entity_id` (misión/nodo)
- `event.payload` (run_id, microaction_id, contexto, detalles)
- `event.kind` (tipado)

## API

- `GET /api/events` (existente) — EventLog.
- `GET /api/missions` — misiones y su estado.
- `GET /api/missions/{id}/trace` — secuencia temporal de una misión.

## Reglas

1. Todo evento es **inmutable** e **inmutable en DB** (EventLog).
2. No se borra un evento: para "corregir" se emite otro event.
3. Observabilidad no usa LLM: es determinista sobre el EventLog.