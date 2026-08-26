# 14 — Aprobación humana

Algunas acciones no deben ejecutarse sin que un humano dé el visto bueno. El
estado `NEEDS_APPROVAL` se activa cuando la microacción lo declara o la policy
lo exige. No se ejecuta nada "pre-aprobado" por defecto.

## Cuándo se requiere (por defecto)

|Acción|Motivo|
|---|---|
|Enviar email|comunicación externa irreversible |
|Publicar (social/web/deploy)|exposición pública |
|Eliminar datos|destructivo |
|Crear lead en CRM (LLM)|datos de contacto |
|Enviar mensaje a cliente|relación con cliente |
|Gasto/compra|monetario |

Politica puede relajarlo por tenant (config), pero nunca para `Delete`/`Publish`/fondos en `deny_by_default`.

## Flujo

```
MicroAccion → needs_approval?
  ├─ no → seguir
  └─ sí → estado NEEDS_APPROVAL
           ↓
       pendiente en mailbox del humano (API `/approvals`)
           ↓
       humano: aprobar / rechazar  (con comentario)
           ↓
       aprobada → RUNNING → ejecuta
       rechazada → CANCELLED (auditado)
```

## API

- `GET /api/approvals/pending` — lista acciones que esperan
- `POST /api/approvals/{id}/decision` → `{decision: "approve"|"reject", note?: str}`

## Registro

Todo queda en el EventLog (`ApprovalRequested`, `Approved`, `Rejected`) con actor=humano.**El LLM nunca se auto-aprueba.** Una solicitud de aprobación es una garantía inalterable de que el sistema actúa dentro de lo permitido por quién lo gobierna: el humano.