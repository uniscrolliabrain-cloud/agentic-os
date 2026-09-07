# UNISCROLL INTERFACE - Cómo correr en local

## 2 terminales necesarias:

### Terminal 1 - Backend (puerto 8000)
```
cd "C:\Users\Alfonso\Desktop\git hub repos\agentic-os"
.venv\Scripts\python.exe run_api.py
```
- API: http://localhost:8000
- Swagger: http://localhost:8000/docs
- Health: http://localhost:8000/  → `{"app":"Agentic OS","status":"ok"}`

### Terminal 2 - Frontend (puerto 5174)
```
cd "C:\Users\Alfonso\Desktop\git hub repos\agentic-os\uniscroll-interface"
npm install   (solo la primera vez)
npm run dev
```
- Frontend: http://localhost:5174
- El proxy de Vite reenvía `/api` → `http://localhost:8000` (no hace falta CORS, aunque ya está habilitado para 5173 y 5174).

## Llaves (ya puestas por defecto en el frontend):
| Campo        | Valor |
|--------------|--------------------------------------------------|
| X-Tenant-Id  | `uniscroll-prod`                                  |
| X-Api-Key    | `sk_uniscroll_test_123`                           |
| X-Admin-Key  | `uniscroll_admin_dev_key_2026` (la del `.env`)    |

- Si ves el punto amarillo **LIVE** = el backend responde y los paneles (chat, eventos, tasks, tools, tenants) muestran datos reales.
- Si ves **Backend offline**, revisa la Terminal 1 (que `run_api.py` esté corriendo) y el CORS.

## Notas
- El backend se crea solo el tenant `uniscroll-prod` vía `scripts\create_tenant.py`.
- Modo preview: si el backend NO está arriba, la interfaz muestra datos de ejemplo (sin romperse).