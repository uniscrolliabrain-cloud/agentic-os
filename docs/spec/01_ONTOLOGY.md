# 01 — Ontología (metamodelo)

Define el vocabulario estructural del mundo digital. Todo dato que el sistema
maneja es una instancia de uno de estos cuatro dominios: **ENTIDAD**, **ACCIÓN**,
**CONTEXTO** o **ESTADO**. Este metamodelo vive en `kernel/ontology/`.

```
WORLD
│
├── ENTITY      → qué son las cosas (nombres)
├── ACTION      → qué se les puede hacer (verbos)
├── CONTEXT     → bajo qué circunstancias (sujetos, clientes, metas)
└── STATE       → en qué momento del ciclo de vida están
```

## ENTITY (lo que existe)

```
ENTITY
├── Person
├── Organization
├── Company
├── Product
├── Service
├── Website
├── URL
├── File
├── Document
├── Dataset
├── Message
├── Email
├── SocialPost
├── Image
├── Video
├── Audio
├── Event
└── Task
```

## ACTION (lo que se hace)

```
ACTION
├── Discover
├── Search
├── Retrieve
├── Read
├── Write
├── Create
├── Transform
├── Analyze
├── Classify
├── Validate
├── Communicate
├── Publish
├── Execute
├── Update
├── Delete
└── Monitor
```

## CONTEXT (el marco)

```
CONTEXT
├── User
├── Client
├── Project
├── Brand
├── Campaign
├── Goal
├── Constraint
└── Permission
```

## STATE (el ciclo de vida)

```
STATE
├── Pending
├── Running
├── Completed
├── Failed
├── Blocked
├── NeedsApproval
└── Cancelled
```

## Reglas del metamodelo (invariantes)

- Todo `Entity` pertenece a una categoría de `ENTITY`.
- Toda operación ejecutable pertenece a una categoría de `ACTION`.
- Toda operación se ejecuta sobre una `ENTITY`, en un `CONTEXT`, y produce un cambio de `STATE`.
- `Policy governs Capability` (GOVERNANCE): ninguna acción escapa a la policy.
- Los invariantes se testean en `kernel/ontology/invariants.py` y `kernel/policy/invariants.py`.