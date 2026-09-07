# UNISCROLL INTERFACE - VSCode x Grok x Brutalist

Branding: UNISCROLL OS - brutalist minimal editorial (black / white / yellow)

## Puertos
- Backend Agentic OS: http://localhost:8000 (Swagger en /docs intacto)
- Este frontend: http://localhost:5174

## Auth real
Arriba pon:
- X-Tenant-Id (slug del cliente, ej: uniscroll-prod)
- X-Api-Key (api_key del cliente guardado en config.credentials.api_key)
- X-Admin-Key (ADMIN_API_KEY de tu .env)

Todos los fetch usan esos headers:
- GET /api/state, /api/events (polling 3s), /api/tasks (polling 3s)
- GET /api/tenants (requiere X-Admin-Key)
- GET /api/conversations, /api/artifacts, /api/drafts, /api/skills, /api/tools
- POST /api/chat {message, conversation_id}
- POST /api/execute {action, params}

## Módulos VS Code + Grok
- Activity Bar 48px negro
- Sidebar Explorer 280px con TENANTS reales + CONVERSATIONS + TIMELINE
- Main Tabs: PROMPT / 01 (chat Laia), AGENT COMPUTER (preview Grok con /workspace, browser clicks, terminal), STATE, EXECUTE
- Bottom Panel: PROBLEMS (failed tasks), OUTPUT (events stream), DEBUG (state), TERMINAL (execute)
- Right Panel 340px: AGENT DETAILS + CONNECTORS @ + SKILLS / + CREDENTIALS STATUS
- Status Bar: BRUTALIST • MINIMAL • EDITORIAL — UNISCROLL.OS — LIVE

## CORS en backend (rest.py)
Añade en src/agentic_os/interfaces/api/rest.py antes de app = FastAPI():

from fastapi.middleware.cors import CORSMiddleware
app = FastAPI(...)
app.add_middleware(
  CORSMiddleware,
  allow_origins=["http://localhost:5174"],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

## Run
cd uniscroll-interface
npm install
npm run dev

Luego con Cline lo conectas: dile que el frontend ya está en 5174 proxyando /api a 8000.
