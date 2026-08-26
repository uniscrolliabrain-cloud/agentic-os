# 03 — Tipos de entidad (ENTITY)

Cada tipo de entidad es un `BaseModel` pydantic (frozen) en `kernel/ontology/entities.py`.
Los campos listados son el mínimo contractual; se pueden añadir campos opcionales
con `Optional[...]` o `Field(default_factory=...)`, nunca quitar.

## Catálogo base

| Tipo | Campos mínimos |
|---|---|
| Person | `name`, `emails: list[str]`, `phones: list[str]`, `organization_id?`, `role?` |
| Organization | `name`, `website?`, `domain?`, `industry?` |
| Company | `legal_name`, `name`, `domain?`, `size?`, `industry?`, `revenue?` |
| Product | `name`, `description?`, `price?`, `category?` |
| Service | `name`, `description?`, `owner?`, `category?` |
| Website | `url`, `title?`, `description?` |
| URL | `url`, `scheme`, `host`, `path`, `query?` |
| File | `path`, `name`, `format`, `size_bytes?`, `hash?` |
| Document | `title`, `content?`, `format`, `source_url?`, `metadata: dict` |
| Dataset | `name`, `columns: list[str]`, `rows: int`, `format`, `source?` |
| Message | `channel`, `sender`, `recipient`, `content`, `timestamp` |
| Email | `from_`, `to: list[str]`, `cc: list[str]`, `subject`, `body`, `id?` |
| SocialPost | `platform`, `content`, `media: list[str]`, `scheduled_at?`, `status` |
| Image | `url?`, `path?`, `prompt?`, `format`, `size_bytes` |
| Video | `url?`, `path?`, `script?`, `duration_sec?`, `format` |
| Audio | `url?`, `path?`, `transcript?`, `format` |
| Event | `type`, `at`, `actor_id`, `entity_id`, `payload: dict` |
| Task | `title`, `description?`, `assignee?`, `status`, `due?`, `dependencies: list[str]` |

## Reglas

- Toda entidad tiene `id: str` (generado por `kernel/types/ids.py:new_id`).
- Toda entidad es inmutable (frozen); los cambios generan una **nueva versión** y un evento, nunca una mutación in-place.
- Las entidades solo se crean/actualizan a través de microacciones del catálogo.
- `dataset`, `document` e `image` pueden contener `metadata: dict` libre, pero las
  claves reservadas (`id`, `created_at`, `mime_type`) no son editables por el LLM.