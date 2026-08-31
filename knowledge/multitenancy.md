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

## Knowledge base por tenant

El asistente frontal (Laia) resuelve la knowledge base según el tenant activo
(resuelto por la cabecera `X-Tenant-Id`):

| Fuente | Ruta | Ámbito |
|---|---|---|
| Compartida | `knowledge/` (raíz del repo) | Todos los tenants |
| Del tenant | `data/tenants/{tenant_id}/knowledge/` | Solo ese tenant |

Cómo se combinan:

1. `knowledge/` es la base compartida (documentación general del producto).
2. Con un tenant real (no el scope anónimo `system`), el asistente construye
   una KB combinada: `KnowledgeBase(directories=[compartida, del_tenant])`.
3. **Precedencia**: si un documento con el mismo título existe en ambas fuentes,
   gana la del tenant (la fuente más específica).

Reglas:

- El tenant anónimo (`system`, sin cabecera) solo ve la base compartida.
- Ningún tenant ve nunca la carpeta de knowledge de otro: la ruta se deriva del
  tenant resuelto en el servidor, nunca del body de la petición.
- Para añadir conocimiento de un cliente: crear
  `data/tenants/{tenant_id}/knowledge/*.md` (o `.txt`); se detecta
  automáticamente (caché por tenant, se recarga al reiniciar el backend).
- TODO(auth): cuando exista OAuth/JWT real, restringir la escritura de estas
  carpetas a usuarios con rol admin del tenant.

## Ejecutar acciones

Para ejecutar una acción hay que tener un cliente activo seleccionado y que su
política lo permita. Flujo: Action → PolicyEngine (¿permitido para este tenant?)
→ Executor (tool correspondiente) → EventLog.