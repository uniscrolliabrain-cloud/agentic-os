# 13 — Permisos

Gobernanza: la **policy gobierna la capability**. Nada se ejecuta sin pasar por `PolicyEngine`.

## Modelo

- **Rol** (`director`, `operator`, `auditor`, …) → permiso.
- **Tenant** (cliente) → su propia config + `enabled_capabilities`.
- **Capability** → sets de microacciones/tools permitidas.
- **PolicyRule** `{capability, effect, requires_roles}` → decide `allow`/`deny`/`require_approval`.

## Flujo de decisión (antes de cada ejecución)

```
LLM propone Intent
  ↓
PolicyEngine.can(capability, roles)
  ├─ allow            → Executor → Tool → EventLog
  ├─ deny             → se rechaza (auditado)
  └─ require_approval → NEEDS_APPROVAL (ver 14)
```

## Defaults de seguridad

- **Deny by default**: si no hay regla, se deniega.
- `Delete` y `Publish` → `require_approval` por defecto.
- El rol `auditor` solo puede `read` (tiene `forbidden_tools=["*"]`).
- El rol `operator` no puede `gmail_send` directamente (lo permite el miniagente con policy específica y aprobación).

## Aislamiento de tools por miniagente

Cada miniagente declara `tools: []` (solo las suyas). Aunque el `Executor` tenga 100 tools, un agente solo usa las suyas: un atacante en `CONTENT_AGENT` no toca el calender ni el CRM.

## Policy del tenant

- `data/tenants/registry.json` persiste `enabled_capabilities` y credenciales por tenant.
- Si un tenant no tiene habilitada una capability → `deny`.
- Compatibilidad: `CommandMap` se controla por capability y policy del tenant (referencia `domains/`).