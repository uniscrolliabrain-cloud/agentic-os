# CLINE PROMPTS - Branquear Backend a Frontend Uniscroll (5174)
# Repo: agentic-os / uniscroll-interface
# Objetivo: dejar `uniscroll-interface` en http://localhost:5174 branqueado 100% a http://localhost:8000 (API + Swagger intacto)

## PROMPT 01 - Fix CORS para 5174

```
Tarea: Añadir puerto 5174 al CORS de FastAPI.

Archivo: src/agentic_os/interfaces/api/rest.py

Busca:
app.add_middleware(
    CORSMiddleware,
    allow_origins=[...

Reemplaza allow_origins por:
["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173", "http://127.0.0.1:5174"]

Criterio de aceptación: app incluye 5174. No toques nada más. Guarda y valida que no hay error de sintaxis.
```

## PROMPT 02 - Verificar .env con ADMIN_API_KEY

```
Tarea: Asegurar .env existe con ADMIN_API_KEY.

Archivo: .env en raíz agentic-os/

Si no existe, créalo con:
ADMIN_API_KEY=uniscroll_admin_dev_key_2026
GEMINI_API_KEY=
GROQ_API_KEY=

Si ya existe, asegúrate que ADMIN_API_KEY no está vacío. Si está vacío, pon uniscroll_admin_dev_key_2026.
No sobrescribas GEMINI_API_KEY si ya tiene valor.

Criterio: .env tiene ADMIN_API_KEY con valor no vacío.
```

## PROMPT 03 - Verificar estructura data/

```
Tarea: Crear carpetas data necesarias si no existen.

Carpetas:
data/
data/tenants/
data/tenants/system/
data/tenants/system/conversations/
data/tenants/system/artifacts/
data/tenants/system/drafts/
data/conversations/
data/eventlog/
data/policies/

Crea con mkdir -p si no existen. No borres nada existente.

Criterio: todas las carpetas existen (ls data/ las muestra).
```

## PROMPT 04 - Verificar endpoints críticos existen

```
Tarea: Verificación de que rest.py expone todos los endpoints que usa el frontend nuevo VS Code x Grok.

Busca en src/agentic_os/interfaces/api/rest.py que existan estos decoradores:
@app.get("/api/state")
@app.get("/api/events")
@app.get("/api/tasks")
@app.get("/api/tenants")
@app.post("/api/tenants")
@app.get("/api/tenants/{tenant_id}")
@app.patch("/api/tenants/{tenant_id}")
@app.delete("/api/tenants/{tenant_id}")
@app.get("/api/conversations")
@app.post("/api/conversations")
@app.get("/api/conversations/{conv_id}")
@app.post("/api/conversations/{conv_id}/messages")
@app.delete("/api/conversations/{conv_id}")
@app.post("/api/chat")
@app.get("/api/skills")
@app.get("/api/tools")
@app.post("/api/execute")
@app.get("/api/artifacts")
@app.get("/api/schedules")
@app.post("/api/schedules")
@app.delete("/api/schedules/{schedule_id}")
@app.get("/api/drafts")

No modifiques nada. Solo reporta en consola si falta alguno.

Criterio: listado de 24 endpoints encontrados, todos OK.
```

## PROMPT 05 - Crear tenant uniscroll-prod real

```
Tarea: Crear tenant de prueba via código para no depender de curl manual.

Crea script temporal scripts/create_tenant.py con:

from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))
from agentic_os.infrastructure.tenancy import TenantRegistry, Tenant, TenantConfig

registry = TenantRegistry()
tenant = registry.get("uniscroll-prod")
if not tenant:
    config = TenantConfig(name="Uniscroll Prod", slug="uniscroll-prod", credentials={"api_key": "sk_uniscroll_test_123"})
    t = Tenant(id="uniscroll-prod", slug="uniscroll-prod", name="Uniscroll Prod", config=config)
    registry.save(t)
    print(f"CREATED id={t.id} slug={t.slug} api_key={t.config.credentials['api_key']}")
else:
    print(f"EXISTS id={tenant.id} slug={tenant.slug} api_key={tenant.config.credentials.get('api_key')}")

Ejecútalo con: python scripts/create_tenant.py

Criterio: tenant uniscroll-prod existe y devuelve api_key. Ese api_key es el que irá en X-Api-Key del frontend.
```

## PROMPT 06 - Verificar frontend uniscroll-interface existe

```
Tarea: Verificar estructura frontend nuevo.

Carpeta: uniscroll-interface/ en raíz del repo

Debe contener:
package.json (name: uniscroll-interface, scripts dev en 5174)
vite.config.js (con proxy /api -> http://localhost:8000 y port 5174)
tailwind.config.js
postcss.config.js
index.html
src/App.tsx (677 líneas, VS Code x Grok x Uniscroll)
src/main.tsx
src/index.css

Si falta vite.config.js, créalo con:
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
export default defineConfig({
  plugins: [react()],
  server: { port: 5174, host: true, proxy: { '/api': { target: 'http://localhost:8000', changeOrigin: true } } }
})

Criterio: todos los archivos existen. Si alguno falta, créalo.
```

## PROMPT 07 - Test de branqueo backend (health + state)

```
Tarea: Levantar backend y testear branqueo real sin frontend.

Pasos:
1. En una terminal: python run_api.py &
2. Espera 3 segundos
3. Haz:
curl http://localhost:8000/
# debe devolver {"app":"Agentic OS","status":"ok"}

curl http://localhost:8000/api/state \
  -H "X-Tenant-Id: uniscroll-prod" \
  -H "X-Api-Key: sk_uniscroll_test_123" \
  -H "X-Admin-Key: uniscroll_admin_dev_key_2026"

Debe devolver 200 con {"role": "...", "event_count": ...}

Criterio: ambos curl 200. Si falla, revisa PROMPT 01 CORS y PROMPT 02 .env.
Mata el proceso después: pkill -f run_api.py o Ctrl+C
```

## PROMPT 08 - Test de branqueo chat (Laia)

```
Tarea: Testear POST /api/chat real con tenant (voz de Laia + background task)

Con backend corriendo (python run_api.py), haz:

curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Id: uniscroll-prod" \
  -H "X-Api-Key: sk_uniscroll_test_123" \
  -H "X-Admin-Key: uniscroll_admin_dev_key_2026" \
  -d '{"message":"hola, test de branqueo"}'

Esperado:
{"reply": "...", "processing": true, "task_id": "task_..."}

Luego verifica que el task se creó:
curl http://localhost:8000/api/tasks \
  -H "X-Tenant-Id: uniscroll-prod" \
  -H "X-Api-Key: sk_uniscroll_test_123" \
  -H "X-Admin-Key: uniscroll_admin_dev_key_2026"

Criterio: devuelve reply + task_id. El frontend usa exactamente este flujo en [PROMPT / 01] y [AGENT COMPUTER].
```

## PROMPT 09 - Test de eventos y tasks polling (Grok Computer)

```
Tarea: Verificar polling que usa el panel AGENT COMPUTER estilo Grok Bot.

Con backend corriendo:

curl http://localhost:8000/api/events \
  -H "X-Tenant-Id: uniscroll-prod" \
  -H "X-Api-Key: sk_uniscroll_test_123" \
  -H "X-Admin-Key: uniscroll_admin_dev_key_2026"

Debe devolver lista (puede estar vacía al inicio).

curl http://localhost:8000/api/artifacts \
  -H "X-Tenant-Id: uniscroll-prod" \
  -H "X-Api-Key: sk_uniscroll_test_123" \
  -H "X-Admin-Key: uniscroll_admin_dev_key_2026"

curl http://localhost:8000/api/tools

Criterio: los 3 endpoints responden 200 con JSON. Son los que usa el frontend cada 3s en OUTPUT y AGENT COMPUTER.
```

## PROMPT 10 - README de branqueo para humano

```
Tarea: Crear README_BRANQUEO.md en uniscroll-interface/ con instrucciones ultra simples para humano que no sabe de código.

Contenido exacto:

# UNISCROLL INTERFACE - Cómo correr en local

## 2 terminales necesarias:

Terminal 1 - Backend (puerto 8000):
cd agentic-os
python run_api.py
# Swagger: http://localhost:8000/docs

Terminal 2 - Frontend (puerto 5174):
cd agentic-os/uniscroll-interface
npm install (solo primera vez)
npm run dev
# Frontend: http://localhost:5174

## Llaves arriba en el frontend:
X-Tenant-Id: uniscroll-prod
X-Api-Key: sk_uniscroll_test_123 (la que generó PROMPT 05)
X-Admin-Key: uniscroll_admin_dev_key_2026 (la del .env)

Si ves punto amarillo LIVE = branqueado.
Si ves Backend offline = revisa Terminal 1 y CORS (PROMPT 01).

Criterio: archivo README_BRANQUEO.md creado en uniscroll-interface/
```
