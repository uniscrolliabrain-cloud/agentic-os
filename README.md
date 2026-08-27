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
| POST   | `/api/chat`                             | PR responde rápido (knowledge base) + orquestador en segundo plano |
| GET    | `/api/tasks`                           | Estado de las tareas de orquestación en background |
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

## Arquitectura de dos velocidades

Para que el usuario nunca espere al razonamiento del orquestador, el chat tiene dos capas:

1. **Asistente frontal (PR)** — con quien habla el usuario. Rápido, natural y con
   **knowledge base** (carpeta `knowledge/`, RAG-lite por palabras clave). Usa
   `GEMINI_CHAT_MODEL` y NO ejecuta ni propone acciones.
2. **Orquestador (back office)** — se dispara en segundo plano tras cada mensaje.
   El rol *director* (GA) propone una `Intent`, el `PolicyEngine` la valida, el
   `Executor` la ejecuta si aplica y todo se registra en el `EventLog`. El usuario
   **nunca habla con el orquestador en su línea de espera**.

```
Usuario escribe
   ├─ FrontAssistant (PR): knowledge base → responde al instante
   └─ [background] Orchestrator: Intent → Policy → Executor → EventLog
```

- Para alimentar la knowledge base, añade/edita markdown en `knowledge/`.
- La UI muestra "⚙️ Orquestador procesando en segundo plano…" y refresca el log al terminar.
- Endpoint auxiliar: `GET /api/tasks` devuelve el estado de las tareas en background.

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

## Connector Kernel (capa de conectividad)

Bajo `src/agentic_os/connectors/` vive el **kernel de conectores**: la frontera de
ejecución cerrada entre los agentes y el mundo real. **Los 44 providers están
creados pero SIN conectar** — el código nunca contiene credenciales; se inyectan
vía `.env`/CredentialStore cuando toque.

```
MiniAgente → capability canónica → Command (Pydantic)
    → CapabilityRegistry → ConnectorRouter → Connector → Provider API
    → resultado normalizado → Pydantic validado → EventLog
```

- **44 conectores** declarados (Google, Microsoft, OpenAI, Anthropic, Gemini,
  HubSpot, Salesforce, Pipedrive, Slack, WhatsApp, Telegram, Meta, LinkedIn,
  TikTok, WordPress, Shopify, GitHub, Vercel, Cloudflare, n8n, Notion, Stripe,
  Twilio, ElevenLabs, DocuSign, Tavily/SerpAPI/Exa/Brave, browser Playwright,
  storage S3/R2/Supabase, PostgreSQL/Redis/MongoDB, Linear/ClickUp/Asana/Jira,
  Vapi/Retell...) con **265 capacidades canónicas** (`crm.contact.create`,
  `email.message.send`, `finance.refund.create`...).
- Un agente solo emite `Command`s pydantic; jamás ve credenciales, endpoints ni
  SDKs. Sin conexión, toda ejecución devuelve un stub controlado
  (`CONNECTOR_NOT_CONFIGURED`) y el dry-run devuelve preview sin efecto.
- Clasificación de riesgo por capability (READ_ONLY, EXTERNAL_COMMUNICATION,
  FINANCIAL, DESTRUCTIVE...), errores normalizados y auditoría lista para
  policy/aprobación humana. Especificación completa en `docs/spec/`.
