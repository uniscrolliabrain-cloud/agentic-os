# Agentic OS - Deterministic Enterprise OS

Kernel = invariantes. LLM proposes, system disposes.

## Principios
- Event Sourcing: EventLog es fuente de verdad, WorldState es derivado
- Policy gobierna Capability, no el agente
- LLM nunca ejecuta directo
- Ontology separa metamodelo (invariante) de vocabulario (extensible por dominio)

## Estructura

```
src/agentic_os/
  kernel/             invariantes, estable, versionado (world, policy, ontology, types)
  cognition/          beliefs, reasoning, planning, memory, skills, roles
  execution/          action, executor, tools (gmail, slack, whatsapp, calendar, scraper, documentation)
  orchestration/      loops, scheduler, coordinator (VSM)
  interfaces/         mcp, api, llm, events
  domains/            clinic, finance (extienden vocabulario)
  infrastructure/     persistence, config, telemetry, tenancy
frontend/             interfaz React + Tailwind (Vite)
tests/                tests de kernel y llm
docs/                 arquitectura, invariantes, ontología, gobernanza
```

## Quickstart

### 1. Backend (FastAPI local)

```bash
pip install -e .
pip install fastapi uvicorn
cp .env.example .env   # rellena GEMINI_API_KEY
uvicorn run_api:app --reload --port 8000
```

API disponible en `http://localhost:8000` (docs en `/docs`).

### 2. Frontend (React + Tailwind)

```bash
cd frontend
npm install
npm run dev
```

Interfaz disponible en `http://localhost:5173`.

### 3. Tests

```bash
pytest
```

## API Endpoints

| Método | Ruta                                    | Descripción                                        |
|--------|-----------------------------------------|----------------------------------------------------|
| GET    | `/api/state`                            | Rol activo y número de eventos en el log           |
| GET    | `/api/events`                           | Lista de eventos auditables (EventLog)             |
| POST   | `/api/chat`                             | Envía mensaje al director → propone una Intent     |
| GET    | `/api/conversations`                    | Lista conversaciones guardadas                     |
| POST   | `/api/conversations`                    | Crea una conversación nueva                        |
| GET    | `/api/conversations/{id}`               | Carga una conversación por id                      |
| POST   | `/api/conversations/{id}/messages`      | Añade un mensaje a una conversación                |
| DELETE | `/api/conversations/{id}`               | Elimina una conversación                           |
| GET    | `/api/tenants`                          | Lista clientes (tenants) registrados               |
| POST   | `/api/tenants`                          | Registra un nuevo cliente                          |
| GET    | `/api/tenants/{id}`                     | Obtiene un cliente por id                          |
| PATCH  | `/api/tenants/{id}`                     | Actualiza nombre/config de un cliente              |
| DELETE | `/api/tenants/{id}`                     | Elimina un cliente                                 |
| GET    | `/api/skills`                           | Lista el catálogo de skills/SOPs                   |
| GET    | `/api/tools`                            | Lista las herramientas disponibles                 |
| POST   | `/api/execute`                          | Ejecuta una acción (LLM→Policy→Executor)          |

Las conversaciones se guardan en `data/conversations/*.json` (persistencia en disco).
Los tenants se guardan en `data/tenants/registry.json`.

## Arquitectura determinista

```
Usuario escribe
   ↓
Orchestrator (rol "director" via LLM) propone una Intent
   ↓
PolicyEngine valida: ¿está permitida la acción para este tenant?
   ↓ (allow)
Executor ejecuta la tool correspondiente (gmail, slack, whatsapp, calendar, scraper...)
   ↓
Todo se registra en el EventLog (auditable)
```

El LLM **nunca ejecuta directamente**: solo propone. La policy decide, el executor ejecuta.
