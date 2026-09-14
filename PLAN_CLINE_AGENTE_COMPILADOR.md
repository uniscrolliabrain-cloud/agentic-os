# PLAN MAESTRO — Tenant02 «agente con llm arquitecto-compilador de tenants con memoria»

> **Documento de planificación detallado** para construir el segundo tenant
> productivo sobre **Agentic OS**: un agente «arquitecto-compilador» que crea
> **tenants nuevos** dentro de este mismo repo, con acceso a GitHub y capacidades
> de coder y arquitecto (loop inspirado en Cline), pero bajo las reglas del
> kernel: **el LLM solo propone Intents; la Policy decide; el Executor ejecuta;
> el EventLog audita**.
>
> Su producto no es software ni servicios al uso: su producto son **tenants
> nuevos**. Empresas, ideas, proyectos o agentes se «mudan» a Agentic OS sin
> tocar el kernel: aportan su ontología, su policy y sus datos; todo lo demás lo
> comparten.
>
> - **Slug del tenant:** `agentic-compiler` · **Dominio:** `compiler` ·
>   **ID de proyecto:** `AGENT_TENANT_COMPILER_CODER`.
> - **Estado:** v1.0 — audit real del repo (fecha 2026-09-14) + plan por fases.
> - **Regla inviolable:** igual que `bor-agencia` — el LLM **nunca** ejecuta
>   nada directamente. Solo propone Intents Pydantic; el kernel valida la forma,
>   la Policy decide el efecto, el Executor ejecuta, el EventLog audita.
> - **Regla del compilador:** el plan vive en `main` como `.md` (vía PR, nunca
>   push directo); el código generado vive en la rama `agentic-os-roo`; la
>   fusión a `main` la aprueba Alfonso (Gate 2 sobre el PR).
> - **Nota de nombre:** `PLAN_CLINE:AGENTE_COMPILADOR.md` contiene `:` (inválido
>   en Windows). Este documento se archiva como `PLAN_CLINE_AGENTE_COMPILADOR.md`
>   manteniendo el título con dos puntos.
> - **Anexo de referencia:** `PLAN_CLINE_total.md` (= «Anexo B FINAL: Contrato
>   Técnico de Adaptación — Cline Tuneado para Compilador de Tenants», v1.1 con
>   CLI + Streamlit + Temporal.io). Se cita por resumen en §9.

## Índice

| #  | Sección |
|----|---------|
| 1  | Contexto y visión de negocio |
| 2  | Decisiones de modelo (la base de todo) |
| 3  | Auditoría del estado actual del código (lo que se reutiliza) |
| 4  | Principios e invariantes del kernel — el «por qué» |
| 5  | Plan de implementación por fases (0 → 10) |
| 6  | Flujo end-to-end: de la idea al tenant vivo |
| 7  | Decisiones pendientes / preguntas abiertas |
| 8  | Glosario |
| 9  | Anexo A: mapa de archivos · Anexo B: contrato del anexo Cline |

---

## 1. Contexto y visión de negocio

Agentic OS es un **kernel modular** con invariantes estables (event sourcing,
policy como gate único, LLM proposer, ontología termo-modelo/vocabulario). Todo
lo demás — connectors, tools, pipelines, cognition, dominios — es **extensión**.

Hoy el repo tiene **un tenant productivo** (`bor-agencia`, plan en
`PLAN_AGENCIA_TENANT.md` y PR #15 pendiente de merge) que demuestra el patrón:
un dominio propio, una policy propia, una knowledge base propia y **cero cambios
en el kernel**. En el camino quedaron endurecidas las piezas que el tenante 2
necesita: `register_entity_types()` explícito (sin side-effects en import),
`EntityRef` unificada, y el `PipelineRunner` canónico con idempotencia de 24h,
`_audit()` y `emit_event()`.

**El tenant 2 explota ese mismo patrón para construir otros tenants.**

### Qué es `agentic-compiler`

Un tenant cuya «empresa» es un **compilador**: recibe una idea en lenguaje
natural (*«quiero un OS agéntico para mi clínica dental que gestione citas,
recordatorios y facturación»*) y produce:

1. Un **plan `.md`** detallado (blueprint) versionado en `main` (PR a main).
2. Una **rama** `agentic-os-roo` con todo el código generado (dominio, policy,
   pipelines, tests, knowledge, datos semilla).
3. Un **PR** con CI en verde, previa aprobación humana de Alfonso (Gate 2).
4. Un **tenant vivo**: registrado en `registry.json`, con su dominio, policy,
   pipelines, knowledge y datos iniciales.

### Reglas de uso (cómo se le pide algo al compilador)

```
Yo (Alfonso) → «Quiero un tenant para [idea en lenguaje natural]»
  └─ chat localhost (Fase 2) o API /api/v1/blueprints (Fase 9)
     → el compilador responde en modo PLAN: propone blueprint, NO toca archivos
  → apruebo el plan (Gate 1)
  → el compilador genera código en agentic-os-roo (modo ACT, Intents con policy)
  → CI en verde
  → PR a main (Gate 2) → yo apruebo/mergeo
```

### Por qué este tenant es interesante

- **Dog-fooding radical.** El compilador es un tenant; el output del compilador
  son tenants. Si el kernel aguanta la recursión, aguanta todo.
- **Cero cambios al kernel.** Igual que BOR: si hay que tocar `kernel/`, la
  feature no está bien modelada.
- **Aprovecha lo que ya existe.** `PipelineRunner`, `Executor`, `PolicyEngine`,
  `TenantRegistry`, `ENTITY_TYPE_REGISTRY`, `register_entity_types`,
  `resolve_client_credentials`, `WebhookReceiver`, `Scheduler`, `Temporal`,
  `FrontAssistant` — todo sirve tal cual.
- **Dos velocidades nativas.** El chat responde al instante (Laia/prompt rápido);
  la compilación corre en segundo plano (pipeline + sandbox + Temporal).
- **Cline-compatible.** El loop de Cline (propose → tool → observe) es
  exactamente el loop del kernel (Intent → Policy → Executor → EventLog). La
  diferencia: aquí el «tool» es siempre una capability canónica y la decisión la
  toma la Policy, no el LLM.

### Cómo se relaciona con `bor-agencia`

| Recurso | Compartido | Propio del tenant |
|---|---|---|
| Kernel | ✅ todo | — |
| Connector Kernel (44 providers) | ✅ | providers nuevos si hacen falta |
| Tools base (`gmail_*`, `drive_*`, `web_*`, etc.) | ✅ | tools de codegen/git/sandbox |
| Pipelines genéricos (`daily_social`, …) | ✅ | pipelines `compile_*` |
| Cognition (beliefs, memory, reasoning) | ✅ | memoria de builds (propia) |
| Roles (`director`, `operator`, `auditor`) | ✅ | rol `compiler` (opcional) |
| Ontología | ❌ | `agencia.*` vs `compiler.*` |
| Policy | ❌ | `bor-agencia.json` vs `agentic-compiler.json` |
| Knowledge base | ❌ | `knowledge/` propia |
| Credenciales | ❌ (GitHub puede ser compartida) | GitHub token del compilador |

---

## 3. Auditoría del estado actual del código (fecha: 2026-09-14)

### 3.1 Lo que ya está y se reutiliza SIN cambios

| Pieza | Dónde | Estado |
|---|---|---|
| `PipelineRunner.tool()` idempotente con `_audit` + `emit_event` | `orchestration/pipelines/runner.py` | ✅ arreglado hoy (commit `a93bd90`) — todo pipeline debe pasar por aquí |
| `Executor` + `PolicyEngine` + `PolicyEvaluator` | `execution/`, `kernel/policy/` | ✅ |
| `register_entity_types()` explícito (fail-closed) + `ENTITY_TYPE_REGISTRY` 9 core | `kernel/ontology/domain_models.py` | ✅ arreglado hoy |
| `EntityRef` unificada + `Entity.kind` | `kernel/ontology/entities.py` | ✅ arreglado hoy |
| `TenantRegistry` + `registry.json` + `TenantConfigPublic` fail-closed | `infrastructure/tenancy/` | ✅ |
| `resolve_client_credentials()` (copias, no referencias) | `infrastructure/tenancy/credentials.py` | ✅ |
| `<policy>.json` por tenant + carga en `PolicyEngine` | `data/policies/`, `kernel/policy/engine.py` | ✅ (patrón de bor-agencia) |
| `handle_user_message(message, tenant_id)` → `Intent` pydantic | `orchestration/orchestrator.py` | ✅ |
| `ACTION_BY_KIND` (mapa determinista intent.kind → action) | `interfaces/api/rest.py` | ✅ |
| Chat `FrontAssistant` (persona «Laia» + KB) | `interfaces/llm/chat.py` | ✅ |
| LLM: `GeminiProvider` → `GroqProvider` → `MockLLMProvider` (sin key = dev offline) | `interfaces/llm/provider.py` | ✅ |
| FastAPI + CORS a Vite (`localhost:5173/5174`) + auth por headers/JWT | `interfaces/api/rest.py` | ✅ |
| Conversaciones persistidas | `data/conversations/` | ✅ |
| WebhookReceiver, Scheduler (APScheduler), Temporal scaffolding | `interfaces/`, `orchestration/` | ✅ |
| EventLog (repo por tenant) + `correlation_id`/`command_id` | `infrastructure/persistence/` | ✅ |

### 3.2 Lo que NO existe todavía (lo crea este plan)

- Dominio `compiler` (entidades, ontology) → Fase 1/3.
- Tools `repo.*`, `git.*`, `sandbox.*`, `codegen.*`, `ci.*`, `tenant.*` → Fase 3.
- Pipelines `compile_*` → Fase 4.
- Policy `agentic-compiler.json` → Fase 1 (mínima) / Fase 5 (completa).
- Endpoints `/api/v1/blueprints`, `/compilations`, `/approvals` → Fase 2 (chat)
  y Fase 9 (cola).
- Knowledge base del tenant → Fase 6.
- `sandbox/` + `cline_adapter/` (Anexo B) → Fase 7.
- `CompilationWorkflow` (Temporal) → Fase 8.
- Frontend del compilador (panel de gate y estado) → Fase 9 (o Fase 2 para el
  chat, ver §5).

### 3.3 Estrellas a no romper (del trabajo de hoy)

1. `src/agentic_os/domains/agencia/__init__.py` no debe volver a registrar
   entidades en import (invariante: sin side-effects en import).
2. `runner.py` no debe volver a perder el dispatch a `PIPELINES`.
3. `EntityRef` no debe volver a duplicarse.
4. Suite completa: **412 passed, 7 skipped, 0 failed** — objetivo: seguir en
   verde en cada fase (una fase termina cuando `pytest -q` no empeora).

---

## 4. Principios e invariantes del kernel — el «por qué»

| # | Invariante | Dónde se aplica |
|---|---|---|
| I1 | El LLM **propone**; la **Policy decide**; el **Executor ejecuta**; el **EventLog audita**. Nunca al revés. | Todo el sistema; el loop del compilador es la prueba de fuego |
| I2 | Fail-closed tipado: un Intent que no valida en pydantic **no se ejecuta** y se reporta con el motivo. | `Intent`, entidades del dominio `compiler` |
| I3 | Default-deny: todo lo que no está `allow` en la policy es `deny`. | `agentic-compiler.json` termina con `* → deny` |
| I4 | Idempotencia por `command_id` (TTL 24h): reejecutar un paso no re-aplica efectos. | `runner.tool()` (ya implementado) |
| I5 | Sin side-effects en import: los dominios registran sus entidades de forma **explícita** (`register_entity_types()` / `register_entities()`), nunca al importarse. | `domains/compiler/…` |
| I6 | Aislamiento de tenants: un tenant A no ve datos/estado/credenciales de B. | `TenantContext`, `TenantRegistry`, cola de approvals |
| I7 | El compilador no puede escribir en el kernel (regla de la propia policy, no del LLM). | path-guard en `repo.file.write.scoped` |
| I8 | Nada se publica a `main` sin PR con CI verde y aprobación humana. | `git.branch.checkout(main)` = deny; `git.pr.create` = require_approval |

**Documentos de referencia:** `docs/INVARIANTS.md`, `docs/spec/00_SYSTEM_PRINCIPLES.md`,
`docs/spec/01_ONTOLOGY.md`, `docs/ARCHITECTURE.md` (arquitectura de dos velocidades),
`knowledge/que_es_agentic_os.md`.

---

## 5. Plan de implementación por fases (0 → 10)

**Regla de oro:** cada fase termina con `pytest -q` en verde y sin empeorar la
suite completa. La **Fase 2 (chat localhost)** es el MVP accesible cuanto antes:
podrás *hablar* con el compilador incluso antes de que «compile» nada.

### Fase 0 — Este plan (documento)

**Entregable:** `PLAN_CLINE_AGENTE_COMPILADOR.md` commiteado en la rama
`agent/cline/agent-tenant-compiler` y, tras auditoría de Alfonso, por PR a `main`.

**Validación:** revisión humana del documento (Gates sobre el propio plan).

---

### Fase 1 — Alta rápida del tenant (testable de inmediato)

**Objetivo:** `TenantRegistry.get("agentic-compiler")` devuelve el tenant y la
policy mínima decide como se espera. *Sin sandbox ni tools nuevas.*

**Archivos:**
- `data/tenants/registry.json` — entrada `agentic-compiler` (domain `compiler`,
  `data_dir=data/tenants/agentic-compiler`, `enabled_capabilities` mínimas,
  `credentials.api_key` tipo `tk_…`).
- `data/policies/agentic-compiler.json` — política MÍNIMA:
  - `allow`: `repo.file.read`, `repo.file.list`, `repo.search`,
    `codegen.blueprint.generate` (produce artefactos, no efectos externos).
  - `require_approval`: `repo.file.write` (por ahora; en Fase 5 se refina con
    path-guard).
  - `deny`: resto (`*`).
- `src/agentic_os/domains/compiler/entities.py` — **3 entidades estrictas**
  (mismo patrón que `agencia`): `TenantIdea` (idea_nl->normalizada),
  `TenantBlueprint` (esquema del tenant propuesto), `CompilationRun` (estado de
  una compilación). Registrar SOLO de forma explícita (I5).
- `src/agentic_os/domains/compiler/ontology.py` — `CompilerDomain` con
  `register_entities()` (compile_ontology → register_entity_types).
- `src/agentic_os/domains/compiler/__init__.py` — solo exports, sin side-effects.
- `tests/domains/test_compiler_tenant.py` — alta/lectura del tenant,
  `TenantConfigPublic` no expone credenciales, política evaluada por
  `PolicyEvaluator` (`repo.file.read` → allow; `git.push` → deny sin rol).

**Validación:** `TenantRegistry.get("agentic-compiler")` ok; tests de la Fase 1
en verde; suite completa sin empeorar.

---

### Fase 2 — MVP CHAT LOCALHOST ⭐ (ya se puede hablar con el compilador)

**Objetivo (prioridad #1 de Alfonso):** un localhost con chat por el que se le
cuenta la idea al compilador y este responde **en modo PLAN** — con el esquema
del blueprint, las zonas del repo que tocaría y las preguntas que haría — **sin
escribir nada**. Aunque el compilador no esté *fully operativo*, el canal de
conversación con su «IA de orquestación» está activo.

**Qué se construye (todo dentro de lo que ya existe, sin tocar el kernel):**
1. **Persona del compilador:** un `system_compiler.md` (prompt) con instrucciones
   de arquitecto-compilador (qué produce un tenant, qué NO se toca,
   contrato de blueprint, workflow git) → se inyecta como
   `system_instruction` del provider y como KB del `FrontAssistant` del tenant.
2. **Tools read-only** (registradas en el ToolRegistry del tenant y mapeadas en
   `ACTION_BY_KIND`/`CANONICAL_ALIASES`):
   - `repo.file.read(path)` — lee archivo (allow).
   - `repo.file.list(path)` — lista directorio (allow).
   - `repo.search(pattern, glob)` — busca en el repo (allow).
   La policy de la Fase 1 ya las permite: el chat **lee y consulta** el repo real
   (ej: «¿cómo está estructurado `domains/agencia`?»), pero **no escribe**.
3. **Endpoint de chat del tenant:** `POST /api/v1/tenants/{tenant}/chat`
   (o `POST /api/v1/chat` con `X-Tenant-Id: agentic-compiler`), reutilizando el
   patrón `handle_user_message` → `Intent` → responder. En modo PLAN el
   orquestador no propone intents de escritura (los descarta antes de la policy);
   solo responde y, si detecta intención de «crear tenant», devuelve un
   `TenantBlueprint` **propuesto** en el propio mensaje.
4. **Persistencia:** conversación del tenant en su `data_dir`
   (`data/tenants/agentic-compiler/chat/…`), separada de las del sistema.
5. **Frontend:** panel «Compilador» en el frontend React/Vite (localhost:5173)
   que apunta al endpoint anterior con los headers del tenant. (Si se prefiere
   Streamlit como en el Anexo B §7.2, es 1 script; la decisión en §7.)

**Validación (criterio de «listo para testear»):**
```
uvicorn agentic_os.interfaces.api.rest:app --reload --port 8000
npm run dev   # frontend  → http://localhost:5173
# o curl:
curl -X POST http://localhost:8000/api/v1/tenants/agentic-compiler/chat \
  -H "X-Tenant-Id: agentic-compiler" -H "X-Admin-Key: <ADMIN_API_KEY>" \
  -d '{"message": "Quiero un OS agéntico para una clínica dental: citas, recordatorios y facturación"}'
```
Respuesta esperada: el compilador devuelve el **esqueleto del blueprint**
(entidades, capabilities, policy sugerida, fases) y pregunta por Gate 1. Funciona
**sin API key** (MockLLM) y mejora con Gemini (`.env`: `GEMINI_API_KEY`).

**Tests:** `tests/interfaces/test_compiler_chat.py` — chat responde en modo PLAN,
no genera intents de escritura, aislamiento por tenant, conversación persistida.

---

### Fase 3 — Entidades completas, tools y capacidades del compilador

**Entidades nuevas** (en `domains/compiler/entities.py`, más allá de la Fase 1):
`ValidationReport`, `GeneratedArtifact`, `SandboxSession` (opcional), además de
`TenantIdea`, `TenantBlueprint`, `CompilationRun`. Registro SIEMPRE explícito.

**Capacidades/provider** (patrón del Connector Kernel):
- `providers/catalog_compiler.py` → provider `compiler`: `repo.file.read/list`,
  `repo.search`, `repo.file.write`, `codegen.blueprint.generate`,
  `codegen.blueprint.validate`, `codegen.domain/policy/pipeline/entity/knowledge`.
- `providers/catalog_git.py` → provider `git`: `git.status`, `git.diff`,
  `git.log`, `git.branch.create/checkout`, `git.commit`, `git.push`,
  `git.pr.create/comment`.
- `providers/catalog_sandbox.py` → provider `sandbox`: `sandbox.create/exec/stop`.
- `providers/catalog_ci.py` → provider `ci`: `ci.pytest.run`, `ci.ruff.run`,
  `ci.mypy.run`.
- `providers/catalog_tenant_admin.py` → provider `tenant_admin`:
  `tenant.register`, `tenant.blueprint.write`.
- Registrar con `PROVIDER_SPECS.update(...)` en `connectors/providers/__init__.py`
  declarando el `risk` de cada una (`READ_ONLY`, `MEDIUM`, `HIGH`,
  `EXTERNAL_COMMUNICATION`, `CRITICAL`).

**Tools (mock determinista `execution/tools/`):** `RepoReadFileTool`,
`RepoWriteFileTool` (con **Path Guard**), `RepoSearchTool`, `GitBranchCreateTool`,
`GitCommitTool`, `GitPushTool`, `GitPrCreateTool`, `SandboxCreateTool`,
`SandboxExecTool`, `CiRunTool`, `BlueprintGenerateTool`, `DomainGenerateTool`,
`TenantRegisterTool`. Reglas duras en cada tool: **jamás tocar el kernel**,
**jamás push/PR sin `require_approval` resuelto**, **jamás logear credenciales**.

**Validación:** `tests/connectors/test_compiler_capabilities.py`,
`tests/connectors/test_compiler_tools.py` — path traversal rechazado, escritura
en kernel rechazada, `risk_class_for("git.push") == "EXTERNAL_COMMUNICATION"`.

---

### Fase 4 — Pipelines del compilador

**Ubicación:** `orchestration/pipelines/` (son pipelines **generales**: producen
tenants; son la librería central, no van en la carpeta del tenant).

| Pipeline | Herramientas | Salida / estado |
|---|---|---|
| `blueprint_from_idea` | `codegen.blueprint.generate` → validación Pydantic | `TenantBlueprint` + evento `BlueprintProposed` |
| `blueprint_validate` | `codegen.blueprint.validate`, `repo.search` | `ValidationReport` (fail-closed) |
| `plan_write` | `repo.file.write` (a `plans/<blueprint_id>.md`) | artefacto `plan.md` |
| `plan_approve` | `ValidationGate` (humano) | `CompilationRun.status = approved` |
| `sandbox_bootstrap` | `sandbox.create` | `SandboxSession` |
| `generate_tenant` | `codegen.domain/policy/pipeline/entity/knowledge` | artefactos en `agentic-os-roo` |
| `tenant_tests_generate` | `codegen.test` (nuevo) | `tests/tenants/test_<slug>.py` |
| `ci_run` | `ci.pytest.run`, `ci.ruff.run`, `ci.mypy.run` | reporte + artefacto |
| `git_publish` | `git.branch.create`, `git.commit`, `git.push` | rama publicada |
| `pr_open` | `git.pr.create` | PR abierto (Gate 2) |
| `compile_tenant` | orquesta los anteriores | `CompilationRun.status = merged` |

Reglas: cada pipeline recibe `command_id = f"{blueprint_id}:{step}"` → la
reejecución dentro del TTL de 24h no re-aplica. Registro con `@register` como el
resto. Todos los MicroActions pasan por `runner.tool()` (camino canónico).

**Validación:** `tests/pipelines/test_pipelines_compiler.py` — un blueprint de
prueba recorre `blueprint_from_idea → ci_run` con mocks, EventLog consistente.

---

### Fase 5 — Policy completa de `agentic-compiler`

**Archivo nuevo (sustituye a la mínima de Fase 1):**
`data/policies/agentic-compiler.json`.

| Capability | Efecto | Motivo |
|---|---|---|
| `repo.file.read/list`, `repo.search`, `repo.file.stat` | `allow` | Lecturas sin riesgo |
| `repo.file.write`, `repo.dir.create` | `allow` **con path-guard** (`plans/`, `src/agentic_os/domains/`, `data/tenants/…`, `tests/tenants/…`) | El path guard es **regla explícita de la policy**, no del LLM |
| `git.status`, `git.diff`, `git.log` | `allow` | Lecturas |
| `git.branch.create`, `git.branch.checkout` (≠ `main`) | `allow` | La rama es efímera |
| `git.branch.checkout` (`main`) | `deny` (invariante I8) | No se toca `main` sin PR |
| `git.commit` | `allow` | — |
| `git.push`, `git.pr.create`, `git.pr.comment` | `require_approval` (rol `director`) | `EXTERNAL_COMMUNICATION` |
| `sandbox.*` | `allow` | Aislado por diseño |
| `ci.*` | `allow` | Solo lecturas + reporte |
| `codegen.*` | `allow` | Producen artefactos, no efectos externos |
| `tenant.register`, `tenant.blueprint.write` | `require_approval` | Cambio persistente |
| `repo.file.write` con path que empieza por `src/agentic_os/kernel/`, `tests/kernel/`, `.env`, `events.jsonl` | `deny` (invariante I7) | Nunca |
| `*` | `deny` | Red de seguridad |

**Nota:** el path guard se implementa con `resource_kind` (el `PolicyEvaluator`
ya lo soporta como patrón); el pipeline pasa `resource_kind = "kernel"` o
`"domain"` según el path resuelto.

**Validación:** `tests/policy/test_compiler_policy.py` — matriz parametrizada;
escribir en kernel → `deny`; push sin rol `director` → `deny`; push con rol →
`require_approval`.

---

### Fase 6 — Alta plena y knowledge base del tenant

**Alta:** entrada completa en `registry.json` (domain `compiler`,
`enabled_capabilities` con todas las de Fases 3-5, `credentials.github.token`
efímero con scope `agentic-os-roo/<blueprint_id>`), directorios del `data_dir`.

**Knowledge base en `data/tenants/agentic-compiler/knowledge/`:**
- `como_se_crea_un_tenant.md` — guía paso a paso referenciando `bor-agencia` como
  ejemplo canónico.
- `contrato_tenant_blueprint.md` — schema del `TenantBlueprint` con ejemplos.
- `reglas_kernel.md` — recordatorio de qué no se toca (invariantes).
- `workflow_git.md` — plan en main (PR), código en `agentic-os-roo`, PR, merge.
- `anexo_cline.md` — versión canónica del Anexo B (ver §9).

**Estructura del `data_dir`:**
```
data/tenants/agentic-compiler/
├── knowledge/        # los .md anteriores
├── blueprints/       # <blueprint_id>.json (TenantBlueprint serializado)
├── runs/             # <run_id>.json (CompilationRun)
├── sandbox/          # plantillas de VM + snapshot
├── gates/            # ValidationGate pendientes
├── artifacts/        # GeneratedArtifact (referencias)
├── chat/             # conversaciones del chat del tenant
└── schedules.json
```

**Validación:** `GET /api/v1/state` con `X-Tenant-Id: agentic-compiler` devuelve
los eventos del tenant; `test_compiler_tenant.py` ampliado.

---

### Fase 7 — Sandbox VM + Cline adaptado (Anexo B)

**Componentes** (dentro del `data_dir`, nunca del kernel):
```
data/tenants/agentic-compiler/sandbox/
├── Dockerfile                # base python:3.11-slim + git + node
├── vm_entrypoint.sh          # monta el repo, checkout agentic-os-roo
├── cline_adapter/            # código de Cline modificado (Anexo B)
│   ├── loop.py               # propose → Intent → policy → runner.tool() → observe
│   ├── tools_bridge.py       # TODAS las acciones pasan por runner.tool()
│   ├── guardrails.py         # máx 30 pasos, 120s/paso, 30min/run, kill-switch
│   ├── intents.py            # ClineIntent (pydantic)
│   ├── prompts/system_compiler.md
│   ├── cli/compiler_cli.py   # CLI del compilador (Anexo B §7.1)
│   ├── ui/app.py             # Streamlit simple (Anexo B §7.2)
│   ├── temporal/workflows.py + activities.py   # CompilationWorkflow durable
│   └── README.md + MANIFEST.md  # qué se copió de Cline y qué se modificó
└── policies/sandbox_limits.json  # límites duros por ejecución
```

**Mapeo del Anexo B (28 tools de Cline → capabilities canónicas), resumen:**

| Acción Cline (real) | Capability canónica | Tool interna | Riesgo |
|---|---|---|---|
| `read_file` | `repo.file.read` | `RepoReadFileTool` | READ_ONLY |
| `write_to_file` | `repo.file.write.scoped` | `RepoWriteFileTool` | MEDIUM (Path Guard) |
| `replace_in_file` | `repo.file.patch` | `RepoPatchTool` | MEDIUM (SEARCH/REPLACE exacto) |
| `apply_patch` | `repo.file.apply_patch` | `RepoApplyPatchTool` | MEDIUM |
| `list_files` | `repo.list` | `RepoListTool` | LOW |
| `search_files` | `repo.search` | `RepoSearchTool` | LOW |
| `list_code_definition_names` | `repo.symbol.search` | `RepoSymbolTool` | LOW |
| `execute_command` (pytest/ruff/mypy) | `ci.pytest.run` | `CiRunTool` | MEDIUM (allowlist) |
| `execute_command` (ls/cat) | `filesystem.list` | `FilesystemTool` | LOW |
| `browser_action`/`web_search`/`web_fetch` | `web.search`/`web.scrape` | `WebSearchTool` | HIGH (allow_net + policy) |
| `use_mcp_tool` | `mcp.call` | `MCPAdapter` | MEDIUM |
| `use_skill`/`use_subagents` | `skill.run`/`agent.delegate` | `SkillRunner` | MEDIUM |
| `ask_followup_question` | `human.approval.request` | `ApprovalTool` | CRITICAL (require_approval) |
| `attempt_completion` | `compilation.complete` | `EmitEventTool` | LOW |
| `git_commit`/`git_push` | `git.commit.scoped` | `GitCommitTool` | EXTERNAL_COMMUNICATION |
| `open_pull_request`/`new_task` | `git.pr.create` | `GitPrCreateTool` | CRITICAL (Gate 2) |

**Path Guard inviolable** — regla explícita en la policy (bloque `deny_kernel`),
no del LLM:
```json
{ "id": "deny_kernel", "capability": "repo.file.write.scoped", "effect": "deny",
  "description": "DENY src/agentic_os/kernel/**, tests/kernel/**, .env, events.jsonl",
  "condition": "params.path.startswith('src/agentic_os/kernel/') or params.path.startswith('tests/kernel/')" }
```
Solo puede escribir en `data/tenants/<new_slug>/` y `src/agentic_os/domains/<new_slug>/`.

**Reglas del loop (Anexo B):** entrada = `BlueprintStep`; salida = `Intent`
Pydantic (nunca ejecución directa); cada paso emite `ActionStarted` /
`ToolCompleted` / `ToolFailed` al EventLog; timeouts y kill-switch; usa
`Agent-Lock` y `Agent-Queue` existentes para no pisar archivos entre agentes
(cline/roo/kilo). `attempt_completion` → `emit_event("CompilationCompleted")`;
`ask_followup_question` → `ApprovalRequest` (Gate 1/2).

**Validación:** `tests/security/test_sandbox_isolation.py` — la VM no accede al
filesystem del host salvo el checkout; no hay red salvo a GitHub; credenciales
del host ausentes; `MANIFEST.md` documenta origen de Cline (v3.8.2 MIT).

---

### Fase 8 — Scheduler y ejecución durable

- **APScheduler:** disparo manual desde API; opcionalmente reintenta runs
  fallidos `blueprint.proposed_at + 1h`.
- **Temporal:** `orchestration/temporal/` ya existe; se añade
  `CompilationWorkflow` con activities por paso (`blueprint_activity`,
  `generate_activity`, `ci_activity`, `publish_activity`) y
  `RetryPolicy(maximum_attempts=3)`.
- **Idempotencia entre disparos:** `command_id` derivado del `run_id`.

**Validación:** crear un run vía API, verlo en
`data/tenants/agentic-compiler/runs/`, ver el artefacto del EventLog.

---

### Fase 9 — API del compilador y cola de aprobaciones

**Nuevos endpoints en `interfaces/api/rest.py`:**

| Método | Ruta | Qué hace |
|---|---|---|
| `POST` | `/api/v1/blueprints` | `{idea_nl, tenant_hint}` → lanza `blueprint_from_idea` → `blueprint_id` |
| `GET` | `/api/v1/blueprints` | Lista blueprints del tenant |
| `GET` | `/api/v1/blueprints/{id}` | Detalle + `plan.md` |
| `POST` | `/api/v1/blueprints/{id}/compile` | Lanza `compile_tenant` (requiere Gate 1 resuelto) |
| `GET` | `/api/v1/compilations` | Lista runs del tenant |
| `GET` | `/api/v1/compilations/{id}` | Detalle + artefactos |
| `POST` | `/api/v1/compilations/{id}/cancel` | Cancela (destruye sandbox, `cancelled`) |
| `GET` | `/api/v1/approvals` | Cola de aprobación — pendientes |
| `POST` | `/api/v1/approvals/{id}/approve` | Aprueba el gate |
| `POST` | `/api/v1/approvals/{id}/reject` | Rechaza el gate |
| `POST` | `/api/v1/tenants/{tenant}/chat` | (Fase 2) chat del compilador |

Frontend: panel con la cola de approvals (Gate 1 / Gate 2) y estado de los runs.

**Validación:** tests de aislamiento — tenant A no ve blueprints/runs de B;
approvals exigen rol `director`; cancelar un run destruye su sandbox.

---

### Fase 10 — Tests y validación final

**Suite nueva (patrón del repo, `pytest` + `pytest-asyncio`):**

| Fichero | Qué valida |
|---|---|
| `tests/tenants/test_agentic_compiler.py` | alta/lectura, `TenantConfigPublic` sin credenciales |
| `tests/domains/test_compiler_entities.py` | entidades estrictas; registro explícito (I5) |
| `tests/policy/test_compiler_policy.py` | matriz completa (Fase 5) |
| `tests/pipelines/test_pipelines_compiler.py` | blueprint → ci_run con mocks |
| `tests/interfaces/test_compiler_chat.py` | chat modo PLAN |
| `tests/connectors/test_compiler_capabilities.py` | registry/provider/risk |
| `tests/connectors/test_compiler_tools.py` | path-guard, kernel deny, no credenciales |
| `tests/security/test_sandbox_isolation.py` | sandbox aislado |
| `tests/bugs/test_compiler_no_side_effects.py` | import del dominio no muta `ENTITY_TYPE_REGISTRY` |

**Cierre:** `pytest -q` completo en verde **sin empeorar** el baseline actual
(412 passed, 7 skipped, 0 failed); PR de la Fase 10 con CI verde.

---

## 6. Flujo end-to-end: de la idea al tenant vivo

**Walkthrough de un blueprint («clínica dental»):**

```
1. Hablas con el compilador (Fase 2 chat o POST /blueprints Fase 9):
   «Quiero un OS agéntico para una clínica dental: citas, recordatorios y facturación»

2. blueprint_from_idea → TenantBlueprint(idea_nl, entities[], capabilities[],
   policy_suggested, phases[]) + evento BlueprintProposed
   └─ el compilador DEBE leer referencias: docs/INVARIANTS.md, domains/agencia,
      bor-agencia.json (patrón canónico) vía repo.read/repo.search (allow)

3. blueprint_validate → ValidationReport (fail-closed):
   ❌ entidades sin kind → se rechaza y se explica (sin tocar nada)
   ✅ plano válido

4. plan_write → plans/dental_clinic.md  (allow con path-guard)

5. Gate 1: cola de aprobación → compilador pide a Alfonso aprobar el plan
   ├─ reject → CompilationRun.cancelled (fin, sin tokens de codegen)
   └─ approve → CompilationRun.approved

6. sandbox_bootstrap → SandboxSession (VM/contenedor con checkout en agentic-os-roo)

7. generate_tenant → ontología, policy, pipelines, tests, knowledge y datos
   semilla SOLO en data/tenants/dental-clinic/, data/policies/dental-clinic.json,
   src/agentic_os/domains/dental/… (Path Guard: kernel = deny incondicional)

8. tenant_tests_generate + ci_run → ci.pytest.run/ruff/mypy EN SANDBOX
   └─ kill switch: si falla, CompilationFailed y dependientes BLOCKED
      (RetryPolicy maximum_attempts=3 en Temporal)

9. git_publish → rama agentic-os-roo (create/commit/push con approval)

10. Gate 2: git.pr.create (require_approval + require_ci_pass) → PR a main
    ├─ Alfonso revisa diff + CI → merge (merge en el PR, no push directo)
    └─ compile_tenant → CompilationRun.status = merged → tenant vivo

11. El EventLog del compilador registra TODOS los pasos (BlueprintProposed,
    Approved, ArtifactGenerated, CompilationCompleted) con correlation_id del run.
```

**Reglas de oro del flujo:**
- Todos los MicroActions pasan por `runner.tool()` (canónico, idempotente).
- El LLM propone Intents; en ningún punto ejecuta o escribe por su cuenta.
- La escritura de `git.push`/`git.pr.*` requiere aprobación con rol `director`.
- `main` solo recibe lo que llega por PR con CI verde.

---

## 7. Decisiones pendientes / preguntas abiertas

| # | Pregunta | Estado / propuesta |
|---|---|---|
| P1 | Anexo Cline disponible | ✅ resuelto — `PLAN_CLINE_total.md` leído; se integra en Fase 7 (mapeo de 28 tools, CLI+Streamlit+Temporal) |
| P2 | `plan.md` en main: ¿push directo o PR? | **PR a main siempre** (D1, veredicto del Anexo B). El compilador usa `git.pr.create` |
| P3 | ¿VM real o Docker basta? | Docker (contrato `sandbox.exec` idéntico); VM real solo si hace falta (Fase 8) |
| P4 | ¿Frontend React o Streamlit para el chat del compilador? | MVP con el frontend React existente (ya hay CORS); Streamlit del Anexo B §7.2 como alternativa portable para arrancar en segundos |
| P5 | `scripts/Agent-Lock`/`Agent-Queue.py` | Verificar existencia real y API antes de Fase 7 (`loop.py` los importa) |
| P6 | ¿`agentic-os-roo` es rama compartida fija o se crea `agentic-os-roo/<blueprint_id>`? | Propuesta: `agentic-os-roo/<blueprint_id>` (paralelismo + scope de token GitHub) |
| P7 | Relación con PR #15 (bor-agencia sin merge) | El compilador se construye en paralelo; el merge de #15 no bloquea Fases 0-2 |
| P8 | Credenciales reales del compilador | `tk_…` local para dev; GitHub token efímero por blueprint en Fase 6+; Gemini API key en `.env` (no versionada) |
| P9 | ¿Rol `compiler` propio o usar `director/operator/auditor`? | Por defecto reutilizar roles existentes; `compiler` es optativo |
## 8. Glosario

- **Compilador:** el tenant `agentic-compiler` que produce otros tenants.
- **Blueprint (TenantBlueprint):** artefacto Pydantic estricto que describe el
  tenant propuesto (entidades, capabilities, policy sugerida, fases).
- **CompilationRun:** entidad de estado de una compilación (proposed → approved →
  running → succeeded/failed/cancelled/merged).
- **Gate:** punto de aprobación humana (Gate 1 = plan; Gate 2 = PR).
- **Path Guard:** regla de la policy (no del LLM) que limita paths de escritura.
- **Sandbox:** VM/contenedor efímero donde el compilador ejecuta código generado.
- **Build:** ciclo completo idea → tenant vivo.

---

## 9. Anexo A: mapa de archivos · Anexo B: contrato del anexo Cline

### Anexo A — Mapa de archivos a crear/modificar

**Nuevos (por fase):**
```
# Fase 1 — alta + entidades
data/tenants/registry.json                          (M)
data/policies/agentic-compiler.json                 (N)
src/agentic_os/domains/compiler/__init__.py         (N)  sin side-effects
src/agentic_os/domains/compiler/entities.py         (N)  TenantIdea, TenantBlueprint, CompilationRun
src/agentic_os/domains/compiler/ontology.py         (N)  CompilerDomain + register_entities()
tests/domains/test_compiler_tenant.py               (N)

# Fase 2 — chat MVP
src/agentic_os/interfaces/llm/prompts/system_compiler.md   (N)
src/agentic_os/execution/tools/repo_*_tools.py              (N)  read/list/search
src/agentic_os/interfaces/api/rest.py                       (M)  POST /chat
tests/interfaces/test_compiler_chat.py                      (N)

# Fase 3 — capabilities/tools
src/agentic_os/connectors/providers/catalog_compiler.py     (N)
src/agentic_os/connectors/providers/catalog_git.py          (N)
src/agentic_os/connectors/providers/catalog_sandbox.py      (N)
src/agentic_os/connectors/providers/catalog_ci.py           (N)
src/agentic_os/connectors/providers/catalog_tenant_admin.py (N)
src/agentic_os/execution/tools/git_*_tools.py, sandbox_*_tools.py, ci_*_tools.py  (N)
tests/connectors/test_compiler_{capabilities,tools}.py      (N)

# Fase 4 — pipelines (generales)
src/agentic_os/orchestration/pipelines/pipeline_compile_tenant.py  (N)
tests/pipelines/test_pipelines_compiler.py                         (N)

# Fase 5 — policy completa
data/policies/agentic-compiler.json                   (M)
tests/policy/test_compiler_policy.py                  (N)

# Fase 6 — knowledge + data_dir
data/tenants/agentic-compiler/knowledge/*.md          (N)

# Fase 7 — sandbox + cline_adapter (Anexo B)
data/tenants/agentic-compiler/sandbox/Dockerfile, vm_entrypoint.sh   (N)
data/tenants/agentic-compiler/sandbox/cline_adapter/{loop,tools_bridge,guardrails,intents}.py (N)
data/tenants/agentic-compiler/sandbox/cline_adapter/cli/compiler_cli.py (N)
data/tenants/agentic-compiler/sandbox/cline_adapter/ui/app.py         (N)
data/tenants/agentic-compiler/sandbox/cline_adapter/temporal/*.py     (N)
data/tenants/agentic-compiler/sandbox/cline_adapter/prompts/system_compiler.md (N)
data/tenants/agentic-compiler/sandbox/policies/sandbox_limits.json    (N)
tests/security/test_sandbox_isolation.py                              (N)

# Fase 8 — Temporal
src/agentic_os/orchestration/temporal/compilation_workflow.py  (N)

# Fase 9 — API
src/agentic_os/interfaces/api/rest.py               (M)  /blueprints /compilations /approvals

# Fase 10 — suite completa de tests
tests/tenants/test_agentic_compiler.py  y demás (ver Fase 10)
```

**NO se toca nunca:** `src/agentic_os/kernel/**`, `docs/INVARIANTS.md` y el
contrato de dominios (`docs/spec/01_ONTOLOGY.md`).

### Anexo B — Contrato del anexo Cline (resumen; documento canónico: `PLAN_CLINE_total.md`)

`PLAN_CLINE_total.md` (= «Anexo B FINAL: Contrato Técnico de Adaptación — Cline
Tuneado para Compilador de Tenants», v1.1 + CLI + Streamlit + Temporal.io) define:

1. **Arquitectura de aislamiento:** `data/tenants/agentic-compiler/sandbox/cline_adapter/`
   (loop.py, tools_bridge.py, guardrails.py, intents.py,
   prompts/system_compiler.md, cli/compiler_cli.py, ui/app.py,
   temporal/workflows.py + activities.py). Cline es «cerebro alquilado
   (plan/act), no actor»: usa `PipelineRunner.tool()` canónico con
   `correlation_id`, `command_id` e idempotencia; respeta `Agent-Lock` y
   `Agent-Queue.py`.
2. **Modos Cline mapeados:** `plan_mode_respond` → genera `TenantBlueprint`
   (en main); `act_mode_respond` → genera código (en `agentic-os-roo`).
   `attempt_completion` → `emit_event("CompilationCompleted")`;
   `ask_followup_question` → `ApprovalRequest` (Gate 1/2).
3. **Puente de 28 tools** (tabla completa en §5 Fase 7 del plan) —
   capabilities canónicas, siempre pasando por policy.
4. **Guardarraíles:** máx 30 pasos/run, timeout 120s/paso, 30min/run,
   10min/activity, kill-switch con `ci.pytest.run -q + ruff + mypy`, budget de
   tokens por blueprint.
5. **Git e interacción multiagente:** plan en main, código en
   `agentic-os-roo`, `Agent-Lock`, Gates 1/2 y cola de approvals.
6. **INVENTARIO (MANIFEST.md):** origen Cline v3.8.2 MIT (`src/core/Cline.ts`,
   `system.ts`, tools TS) → adaptación; **eliminados** browserTool (SSRF) y
   credentialStore (el `CredentialStore` cifrado del kernel es el único).
7. **CLI + Streamlit + Temporal.io:** `compiler_cli.py` (interactivo),
   `ui/app.py` (Streamlit), área Temporal para prompts/pipelines encolados.

---

*Fin del documento v1.0 — `PLAN_CLINE_AGENTE_COMPILADOR.md`.*
Próximo paso: revisión de Alfonso → merge del plan a `main` → **Fase 1**.