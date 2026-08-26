# Multi-tenant (clientes)

AGENTE OS soporta varios clientes (tenants). Cada tenant tiene:

- nombre y dominio (slug)
- configuración propia (config)
- políticas de ejecución (permitido / denegado)

Los tenants se gestionan desde la interfaz (botón "+ Registrar cliente") o vía API:

- GET /api/tenants → lista
- POST /api/tenants → crea
- GET /api/tenants/{id} → detalle
- PATCH /api/tenants/{id} → actualiza nombre/config
- DELETE /api/tenants/{id} → elimina

Los datos se persisten en `data/tenants/registry.json`.

## Ejecutar acciones

Para ejecutar una acción hay que tener un cliente activo seleccionado y que su
política lo permita. Flujo: Action → PolicyEngine (¿permitido para este tenant?)
→ Executor (tool correspondiente) → EventLog.