
# BUILD PLAN - De andamio a sistema

> Fuente de verdad para la construccion del runtime de Agentic OS.
> Reemplaza a SPEC_UPGRADE_PLAN.md como plan maestro. El anterior
> queda como referencia historica del trabajo C0-C7d.
>
> Creado 2026-09-18. Version 1. Autor: sesion de diseno.
> Dirigido a: cualquier agente o persona que retome el repo.

---

## INDICE

0. Como leer este documento
1. Que construimos (una pagina)
2. Principios (filosofia del sistema)
3. Modelo mental (las 6 capas)
4. Contratos (schemas que cierran el sistema)
5. Decisiones pendientes con propuestas
6. Bloques de construccion (19)
7. Vertical slice (test de aceptacion)
8. Sistema on/off de infraestructura
9. Sistema de trabajo
10. Anti-repeat (4 tablas de tracking)
11. Glosario y referencias

---

## 0. Como leer este documento

Este documento es la fuente unica del plan de construccion del
runtime. El chat es donde se discute; este fichero es donde se
fija. Se actualiza al cerrar cada bloque del apartado 6.

### Que es este documento

- El mapa completo de lo que falta construir.
- El contrato de cada capa del sistema.
- El tracking de estado de cada bloque.
- El registro de decisiones con propuestas.
- El plan de test de aceptacion (vertical slice).

### Que NO es este documento

- No es una spec de comportamiento (eso vive en docs/spec/*).
- No es un changelog (eso vive en CHANGELOG.md).
- No es un estado del repo (eso vive en docs/STATUS.md).
- No es una auditoria (eso vive en docs/audits/*).

### Como se actualiza

Al cerrar un bloque:

1. Cambiar Estado: PENDING -> DONE en la tabla del bloque.
2. Anadir los commits en la columna Commits.
3. Si hubo decisiones, actualizarlas en el apartado 5.
4. Si hubo skills nuevas, anadirlas a la tabla del apartado 10.
5. Si hubo conectores, anadirlos a la tabla del apartado 10.

### Como se lee un bloque

Cada bloque del apartado 6 tiene:

- **Objetivo**: que se logra.
- **Entrada**: que necesita para arrancar (bloques previos, decisiones).
- **Salida**: artefactos que produce (ficheros, schemas, tests).
- **Test**: como se prueba que esta hecho.
- **Decisiones**: que hay que firmar antes de abrir el bloque.
- **Estado**: PENDING | IN_PROGRESS | BLOCKED | DONE.
- **Commits**: referencias git cuando este cerrado.

---

## 1. Que construimos (una pagina)

### 1.1 El objetivo en una frase

> Construimos la infraestructura que permite ejecutar cualquier
> skill, con cualquier agente, para cualquier tenant, contra
> cualquier conector real.

### 1.2 Que NO construimos

No construimos un vertical especifico. Construimos el sistema que
hace posibles todos los verticales. El vertical slice del apartado
7 es el TEST DE ACEPTACION en mundo real, no un build aparte.

### 1.3 Que NO se construye ahora

- Docker-compose productivo.
- Temporal en runtime.
- Supabase en runtime.
- JWT/Auth multi-usuario.
- Dashboard Grafana.

Todo eso queda como on/off (apartado 8). Default off.
Se activa cuando haya clientes reales o necesidad operativa.

### 1.4 La ley fundacional

> LLM PROPONE. SISTEMA DISPONE.
>
> - El LLM nunca ejecuta. Propone Intent, texto, clasificacion.
> - El sistema valida (pydantic), decide (policy), ejecuta (Python),
>   audita (EventLog).
> - Las tools NO las toca la IA. Son Python, ejecutadas por Executor,
>   gobernadas por Policy.
> - Los SOPs, pipelines y skills son codigo Python. El LLM solo entra
>   en los puntos declarados explicitamente como `mode="llm"`.

### 1.5 Por que es urgente

Hoy el repo es un andamio:

- 674 tests verdes, casi todos estructurales (los tipos encajan).
- 44 conectores stubs sin conectar.
- 5 agentes sin SOP real (solo id + name + listas).
- 65+ microacciones en docs, ~15 en codigo.
- Orquestador con 2 caminos paralelos sin cablear (viejo funciona,
  nuevo testeado pero no usado en runtime).
- 0 conectores reales.
- 0 flujos end-to-end con mundo real.

Este plan convierte el andamio en edificio.

---

## 2. Principios (filosofia del sistema)

### 2.1 Los 15 principios

| # | Principio | Origen |
|---|---|---|
| 1 | Kernel = invariantes. No se toca sin Kernel Boundary Rule. | README |
| 2 | LLM propone, sistema dispone. | README |
| 3 | Spec es ley. Contradiccion spec-codigo -> se corrige spec. | docs/spec/00 |
| 4 | Kernel Boundary Rule: las 5 condiciones para tocar kernel. | docs/spec/00 |
| 5 | Spec Contradiction Rule: si spec contradice codigo, se para. | docs/spec/00 |
| 6 | Nada inventado sin decision explicita. | docs/DECISIONS.md |
| 7 | Skills comunales, tenants instancian. | este plan |
| 8 | Orchestrator es Python, no LLM. Ensambla, valida, dispone. | este plan |
| 9 | Laia != orchestrator. Laia explica, no ejecuta. | este plan |
| 10 | Infra on/off desde dia uno. | este plan |
| 11 | Observabilidad gratis ahora, migrable despues. | este plan |
| 12 | El vertical es test de aceptacion, no build. | este plan |
| 13 | Construimos infra para todo, no accion por accion. | este plan |
| 14 | Model router proxy interno (free-tier). | este plan |
| 15 | Cada agente y cada skill pueden declarar modelo preferido. | este plan |

### 2.2 Reglas detalladas

#### 2.2.1 Kernel Boundary Rule

El kernel solo puede modificarse si CUMPLE LAS CINCO:

1. Es universal (aplica a todo dominio).
2. Es necesaria para una invariante del sistema.
3. No depende de ningun dominio.
4. No introduce conocimiento de negocio.
5. Mantiene compatibilidad con los contratos existentes.

Toda modificacion del kernel entra en PR separado, con test propio,
`pytest tests/kernel/` verde antes y despues, y
`test_no_kernel_imports_domains` verde.

#### 2.2.2 Spec Contradiction Rule

Si dos specs se contradicen, o una spec contradice el codigo sin
decision cerrada, la implementacion se detiene:

```
SPEC A != SPEC B
   |
   v
STOP
   |
   v
decision explicita en docs/DECISIONS.md
   |
   v
spec actualizada
   |
   v
implementacion
```

Nunca el agente que escribe codigo resuelve la contradiccion
implicitamente.

#### 2.2.3 Regla de oro del runtime

En un skill, cada paso declara su `mode`:

| mode | Que hace | Quien ejecuta |
|---|---|---|
| `tool` | Ejecuta `tool_id` con `input` | Python (Executor) |
| `llm` | Llama LLM con prompt y schema | LLM propone, Python valida |
| `validate` | Reglas Python | Python |
| `branch` | Expresion Python declarativa | Python |
| `handoff` | Pasa control a otro agente | Python (orquestador) |

El LLM nunca controla el flujo. El flujo es Python. El LLM solo
rellena los puntos marcados `llm`.

#### 2.2.4 Que puede y que no puede el LLM

**Puede**:

- Proponer un `Intent(kind, payload)` validable contra catalogo.
- Generar texto (email, copy, resumen) que se valida contra schema.
- Clasificar (email, lead, documento) con schema cerrado.
- Proponer un plan de skills (que el sistema valida antes de ejecutar).
- Explicar al usuario lo que ha pasado (Laia).

**No puede**:

- Ejecutar tools.
- Decidir policy.
- Emitir `TaskPlan` directo (solo el planner Python).
- Emitir `Handoff` directo.
- Auto-aprobarse.
- Inventar skills o tools fuera del catalogo.
- Controlar el flujo de un skill.

---

## 3. Modelo mental (6 capas)

### 3.1 Diagrama

```
+----------------------------------------------------------+
| LAIA (LLM)                                               |
|  Habla con el usuario. Explica el runtime. Personalizada |
|  por tenant. NO ejecuta. NO decide. PUEDE proponer      |
|  Intent al orquestador (opcional).                       |
|  Input:  mensajes usuario + read-model runtime           |
|  Output: texto al usuario + Intent propuesto (opcional)  |
+----------------------------------------------------------+
                            |
                            v
+----------------------------------------------------------+
| ORCHESTRATOR (Python)                                    |
|  - Recibe triggers (mensaje, email, foto, webhook, cron) |
|  - Extrae Intent (determinista o LLM-propuesto-validado) |
|  - Construye TaskPlan via build_task_plan()              |
|  - Despacha via TaskScheduler                            |
|  - Ensambla output_schema de cada paso (SchemaAssembler) |
|  - Persiste misiones y aprobaciones                      |
+----------------------------------------------------------+
                            |
                            v
+----------------------------------------------------------+
| AGENTS (perfil Python + rol LLM limitado)                |
|  - Cada agente es manager de un departamento.            |
|  - Declara: skills permitidas, SOP, QA, handoffs,        |
|    roles, approvals.                                      |
|  - Ejecuta SOP (Python). En puntos de decision, LLM      |
|    propone; sistema valida antes de continuar.           |
+----------------------------------------------------------+
                            |
                            v
+----------------------------------------------------------+
| RUNTIME (Python)                                         |
|  - SkillRunner: ejecuta pasos del skill                  |
|  - Executor: policy -> tool                              |
|  - Connectors: real o stub, on/off                       |
|  - Memory: tenant-scoped                                 |
|  - Log + Trace: mission->plan->node->skill->tool         |
+----------------------------------------------------------+
                            ^
                            |  consume
+----------------------------------------------------------+
| SKILLS (biblioteca comunal)                              |
|  prompt + few-shots + input/output schemas               |
|  + steps[modes] + tool_id + validacion + postcond        |
|  + tenant_overrides + department.                        |
+----------------------------------------------------------+

+----------------------------------------------------------+
| TENANT COMPILER (fabrica, es un tenant)                  |
|  Dado raw data + ontologia de un tenant nuevo,           |
|  genera sus pipelines = combinaciones de skills          |
|  comunales + policies + capabilities.                    |
+----------------------------------------------------------+
```

### 3.2 Las 6 capas, una por una

#### 3.2.1 SKILLS - biblioteca comunal

La unidad minima operativa del sistema. NO son por tenant.
Cada tenant las habilita y parametriza via `tenant_overrides`.

Un skill combina:

- Identidad: `id`, `version`, `description`, `department`.
- Prompt: `prompt_template` + `few_shots`.
- Contratos: `input_schema` + `output_schema` (pydantic frozen).
- Pasos: lista de `SkillStep` con `mode` y parametros.
- Herramienta: `tool_id` si aplica.
- Validacion: `preconditions`, `postconditions`, `validation_rules`.
- Errores: `error_states`, `retry_policy`, `timeout_seconds`.
- Overrides: `tenant_overrides` (tono, idioma, restricciones).
- Economia: `cost_hint` para el model router.

#### 3.2.2 ORCHESTRATOR - assembler (Python)

No decide. Ensambla y dispone.

Sus responsabilidades:

- Recibir triggers y normalizarlos.
- Extraer Intent (determinista o LLM-propuesto-validado).
- Construir el TaskPlan con `build_task_plan(intent, catalog)`.
- Despachar el plan con `TaskScheduler`.
- **Ensamblar el output_schema**: cuando un paso `mode="llm"`
  devuelve texto libre, el `SchemaAssembler` lo empaqueta en el
  schema pydantic declarado. Si no valida, error. No se fabrica.
- Persistir misiones y aprobaciones.
- Emitir eventos al EventLog con `mission_id` propagado.

El orquestador es un modulo Python puro. Su unica interaccion con
el LLM es via los puntos `mode="llm"` de los skills.

#### 3.2.3 AGENTS - managers de departamento

Un agente es:

- Un **perfil Python declarativo** (Pydantic):
  - `id`, `name`, `department`.
  - `skills_allowed`: que skills puede invocar.
  - `sop`: pipeline Python que sigue.
  - `qa_rules`: criterios de aceptacion del output.
  - `handoffs`: a que otros agentes puede pasar el trabajo.
  - `roles`: que roles humanos pueden invocarlo.
  - `approvals`: que acciones requieren aprobacion humana.
  - `preferred_model`: modelo LLM preferido (opcional).
  - `context`: que ve al arrancar (memoria, beliefs, tenant).

NO es un LLM autonomo. Es un manager que ejecuta su SOP (Python)
con puntos de decision donde el LLM propone y el sistema valida.

Ejemplo:

```
CONTENT_AGENT
  department: content
  skills_allowed: [research.web_search, content.outline,
                   content.draft, content.qa, content.metadata]
  sop: content.campaign_pipeline
  qa_rules: [no_fabricated_facts, min_word_count, tone_match]
  handoffs: [communication_agent, social_agent]
  approvals: [publish]
  preferred_model: gemini-flash
```

#### 3.2.4 RUNTIME - muscle (Python)

El ejecutor real. Todo Python.

- **SkillRunner**: recibe `(skill_id, input, context)`, ejecuta
  paso a paso, valida antes y despues de cada paso, aplica retry,
  persiste estado intermedio para resume.
- **Executor**: `policy -> tool`. Ya existe, se reusa.
- **Connectors**: real o stub. On/off por env var.
- **Memory**: `CognitionStore` scoped por (tenant, agent).
- **Log + Trace**: EventLog con `mission_id` propagado en toda la
  jerarquia `mission -> plan -> node -> skill -> tool`.

#### 3.2.5 LAIA - capa PR

Laia NO es el orquestador. Es la cara visible.

Sus responsabilidades:

- Hablar con el usuario en su idioma y tono (via overrides del
  tenant).
- Ver el read-model del runtime (misiones activas, planes, skills
  en ejecucion, aprobaciones pendientes).
- Explicar lo que esta pasando con lenguaje natural.
- **Opcionalmente** proponer un Intent al orquestador cuando el
  usuario pide algo accionable.

Laia NUNCA ejecuta tools. NUNCA decide policy. NUNCA emite
TaskPlan. Si propone un Intent, el orquestador lo valida antes de
actuar.

Modo de operacion (dos velocidades):

- Laia responde al usuario rapido, sin esperar al runtime.
- El orquestador trabaja en background, actualizando el read-model.
- Laia consulta el read-model cuando el usuario pregunta "que tal".

#### 3.2.6 TENANT COMPILER - fabrica

Es un tenant especial (`agentic-compiler`).

Dado un tenant nuevo:

- Recibe raw data + ontologia declarada.
- Genera los pipelines del tenant = combinaciones validas de
  skills comunales.
- Genera policies especificas del tenant.
- Registra capabilities habilitadas.
- Prepara knowledge base inicial.

El compilador es Python. Su output son ficheros del tenant
(pipelines, policies, capabilities), no ejecucion.

### 3.3 Flujo resumido (una mision)

```
1. Usuario escribe -> Laia responde rapido (front).
2. Laia (o trigger externo) propone Intent al orquestador.
3. Orquestador valida Intent contra catalogo.
4. Orquestador construye TaskPlan (build_task_plan).
5. Orquestador despacha plan (TaskScheduler).
6. Para cada nodo del plan:
   a. SkillRunner ejecuta el skill del agente.
   b. Pasos tool -> Executor -> tool.
   c. Pasos llm -> LLM propone -> SchemaAssembler valida.
   d. Pasos validate/branch -> Python.
7. Eventos al EventLog con mission_id.
8. Si algun paso requiere approval -> pausa + notifica.
9. Humano aprueba -> resume.
10. Mision termina -> Laia puede explicar al usuario.
```

---

## 4. Contratos (schemas que cierran el sistema)

Todos los contratos son Pydantic v2 (frozen + extra=forbid). Viven en
`src/agentic_os/cognition/skills/schema.py` (nuevos) o en los modulos
actuales que se reutilizan.

### 4.1 SkillSchema

```python
class SkillStep(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    order: int
    name: str
    mode: Literal["tool", "llm", "validate", "branch", "handoff"]
    # mode="tool"
    tool_id: Optional[str] = None
    tool_input_template: Optional[Dict[str, Any]] = None
    # mode="llm"
    prompt_template: Optional[str] = None
    response_schema: Optional[Dict[str, Any]] = None
    preferred_model: Optional[str] = None
    # mode="validate"
    validation_rules: List[str] = Field(default_factory=list)
    # mode="branch"
    condition: Optional[str] = None
    then_step: Optional[int] = None
    else_step: Optional[int] = None
    # mode="handoff"
    to_agent_id: Optional[str] = None
    payload_ref: Optional[str] = None
    # Comunes
    output_key: str = "output"
    optional: bool = False
    timeout_seconds: int = 60
    retry_policy: Dict[str, Any] = Field(default_factory=dict)

class SkillSchema(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    id: str                       # ej. "communication.write_email"
    version: str                  # semver: "1.0.0"
    description: str
    department: str               # taxonomia (ver 4.7)
    purpose: str
    # Prompt (para pasos mode="llm" dentro del skill)
    prompt_template: Optional[str] = None
    few_shots: List[Dict[str, Any]] = Field(default_factory=list)
    # Contratos
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    output_schema: Dict[str, Any] = Field(default_factory=dict)
    # Ejecucion
    steps: List[SkillStep] = Field(default_factory=list)
    preconditions: List[str] = Field(default_factory=list)
    postconditions: List[str] = Field(default_factory=list)
    validation_rules: List[str] = Field(default_factory=list)
    error_states: List[str] = Field(default_factory=list)
    retry_policy: Dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: int = 60
    # Overrides por tenant (tono, idioma, restricciones)
    tenant_overrides: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    # Economia (model router)
    cost_hint: Optional[str] = None  # "cheap" | "medium" | "expensive"
    preferred_model: Optional[str] = None
```

### 4.2 SkillExecution

```python
class SkillExecutionStep(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    order: int
    name: str
    mode: str
    state: str                    # de StateMachine
    input: Dict[str, Any]
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: datetime
    finished_at: Optional[datetime] = None
    attempt: int = 1

class SkillExecution(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    id: str                       # execution_id
    skill_id: str
    skill_version: str
    tenant_id: str
    agent_id: str
    mission_id: str
    plan_id: str
    node_id: str
    correlation_id: str
    command_id: str
    steps: List[SkillExecutionStep] = Field(default_factory=list)
    final_state: str
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: datetime
    finished_at: Optional[datetime] = None
```

### 4.3 MissionTrace

```python
class TraceNode(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    node_id: str
    agent_id: str
    depends_on: List[str]
    state: str
    skill_execution_ids: List[str]
    started_at: Optional[datetime]
    finished_at: Optional[datetime]

class MissionTrace(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    mission_id: str
    tenant_id: str
    plan_id: str
    owner_user_id: Optional[str]
    nodes: List[TraceNode] = Field(default_factory=list)
    skill_executions: List[SkillExecution] = Field(default_factory=list)
    events: List[EventRef] = Field(default_factory=list)
    started_at: datetime
    finished_at: Optional[datetime] = None
    final_state: str
    total_cost_usd: float = 0.0
    total_tokens: int = 0
```

### 4.4 ModelRequest / ModelResponse

```python
class ModelRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    prompt: str
    system_instruction: Optional[str] = None
    response_schema: Optional[Dict[str, Any]] = None
    preferred_model: Optional[str] = None
    tenant_id: Optional[str] = None
    correlation_id: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: float = 0.2
    cost_hint: Optional[str] = None

class ModelResponse(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    text: str
    structured: Optional[Dict[str, Any]] = None
    provider: str
    model: str
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0
    fallback_used: bool = False
    cache_hit: bool = False
```

### 4.5 Trigger (lista cerrada)

```python
TriggerType = Literal[
    "user_message",       # mensaje de Laia al orquestador
    "email_received",     # Gmail / Outlook
    "photo_received",     # imagen subida por el usuario
    "webhook",            # Slack / Discord / Stripe
    "cron",               # APScheduler
    "schedule",           # schedule declarado por el tenant
]
```

### 4.6 ApprovalRequest

```python
class ApprovalRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    id: str
    tenant_id: str
    mission_id: str
    node_id: str
    skill_id: str
    action: str
    reason: str
    payload_preview: Dict[str, Any]
    requested_at: datetime
    requested_by_agent: str
    status: str                    # pending | approved | rejected
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    note: Optional[str] = None
```

### 4.7 Taxonomia de departamentos (cerrada)

| Department | Que cubre |
|---|---|
| `communication` | Emails, Slack, WhatsApp, Discord, notificaciones |
| `research` | Busqueda web, investigacion, validacion de fuentes |
| `crm` | Contactos, empresas, deals |
| `sales` | Prospeccion, scoring, outreach, secuencias |
| `content` | Briefs, articulos, copy, guiones |
| `analytics` | KPIs, informes, anomalias |
| `creative` | Imagenes, audio, video |
| `automation` | Workflows, schedulers, webhooks |
| `database` | Queries, schema, migrations |
| `software` | Codigo, tests, deploys |
| `documents` | PDFs, DOCX, extraccion |
| `social` | Posts, carruseles, reels |
| `marketing` | Campanas, anuncios, audiencias |
| `data` | ETL, normalizacion, validacion |
| `platform` | Skills internos (compilador, etc.) |

### 4.8 Convenciones

- Id de skill: `<department>.<snake_case>`.
- Id de agente: `<snake_case>_agent`.
- Version de skill: semver.
- Fecha/hora: timezone-aware UTC (via `now_utc()`).
- Import del kernel: via `kernel.*`.
- Import de dominio: no cruza a kernel.

---

## 5. Decisiones pendientes con propuestas

Cada decision sigue el formato de docs/DECISIONS.md. Las nuevas seran
D19+ cuando se firmen. Aqui se listan con propuesta.

### 5.1 Bloqueantes de arranque

#### D19 - Estructura de un Skill

**Pregunta**: que campos tiene un skill, exactamente?
**Propuesta**: los del apartado 4.1. Prompt + few-shots +
input/output schemas + steps + tool_id + validacion + postcond
+ tenant_overrides + department + cost_hint.
**Faltante a decidir**:

- Prompt como string o como template con DSL. Propuesta: string
  con `{variable}` interpolacion estandar.
- Few-shots como lista de dicts. Propuesta: si, cada dict tiene
  `input` y `output`.

#### D20 - Idioma de prompts

**Pregunta**: prompts en espanol, ingles, o por tenant?
**Propuesta**: base en ingles (mejor rendimiento LLM general),
overrides por tenant en su idioma via `tenant_overrides`.

#### D21 - Versionado de skills

**Pregunta**: skill global con overrides, o por tenant?
**Propuesta**: global + overrides. Un skill es universal; un
tenant puede cambiar prompt/tono/restricciones pero NO la
estructura de pasos.

#### D22 - Model router: proveedores free-tier

**Pregunta**: que proveedores ahora?
**Propuesta**:

- Gemini 1.5 Flash (Google, free tier generoso).
- Groq (Llama 3.3 70B, free tier).
- Hugging Face Inference API (fallback).
- Ollama local (dev, sin internet).

#### D23 - Bloque de arranque

**Pregunta**: arrancamos por bloque 0b (on/off) o 1 (Skill)?
**Propuesta**: 0b primero. Es rapido y desbloquea todo lo demas.

### 5.2 Bloqueantes de bloques posteriores

#### D24 - Worker de misiones

**Propuesta**: asyncio para misiones (concurrencia por tenant),
APScheduler para schedules. Temporal on/off para production.
**Bloque**: 7.

#### D25 - Embeddings para memoria

**Propuesta**: local con `sentence-transformers`.
**Bloque**: 3 y 6.

#### D26 - Web Search proveedor

**Propuesta**: Brave Search API (free tier) + fallback a
DuckDuckGo.
**Bloque**: 11.

#### D27 - Los 2 tenants del vertical

**Propuesta**:

- `bor-agencia` (ya existe, dominio agencia, caso real).
- `clinic-test` (nuevo, dominio clinic, para probar compilador).

**Bloque**: 9.

#### D28 - Observabilidad

**Propuesta**:

- Logs: estructurados JSON + `structlog`.
- Metricas: Prometheus + Grafana Cloud free tier.
- Tracing: OpenTelemetry + Jaeger local.

**Bloque**: 12.

#### D29 - Laia: polling o subscribe

**Propuesta**: read-model persistido + polling ligero.
WebSocket en production.
**Bloque**: 0c.

#### D30 - SchemaAssembler

**Propuesta**:

1. LLM llamado con `response_schema` (structured output nativo).
2. Si no soporta, prompt + parseo JSON.
3. Output pasa por `pydantic.validate_json()`.
4. Si no valida, se reintenta 1 vez con feedback del error.
5. Si sigue sin validar, `ValidationFailed`.

**Bloque**: 7.

#### D31 - Que pasa si no existe skill

**Propuesta**: router devuelve `NoSkillFound`. Laia lo comunica.
No se inventa skill en runtime.
**Bloque**: 4.

#### D32 - Laia propone Intent?

**Propuesta**: si, solo via `Intent`. Laia nunca ejecuta.
**Bloque**: 0c.

#### D33 - Acumulacion de intents -> task list

**Propuesta**:

- `IntentQueue` en `data/tenants/<tid>/intents.jsonl`.
- `IntentAggregator` agrupa por afinidad.
- `TaskScheduler` consume planes.

**Bloque**: 7.

#### D34 - Foto como trigger

**Propuesta**: `photo_received` -> Vision LLM (Gemini Vision o
GPT-4V) -> texto + intent -> mismo validador.
**Bloque**: 7 + 11.

#### D35 - Como Laia ve el runtime

**Propuesta**: read-model `TenantRuntimeView` con misiones activas,
aprobaciones pendientes, ultimos eventos, metricas resumidas.
**Bloque**: 0c.

#### D36 - Modelo preferido por agente vs skill

**Propuesta**:

1. Paso declara `preferred_model` -> ese.
2. Skill declara `preferred_model` -> ese.
3. Agente declara `preferred_model` -> ese.
4. `ModelRouter` decide por `cost_hint` y disponibilidad.

**Bloque**: 0.

#### D37 - Skills como codigo o como datos

**Propuesta**: `.py` para el repo. YAML solo si un tenant necesita
declarar skills sin tocar codigo.
**Bloque**: 1.

#### D38 - Como se testea una skill

**Propuesta**:

- Test unitario input.
- Test unitario output.
- Test pasos `tool` con mocks.
- Test pasos `llm` con stub determinista.
- Golden test con LLM real (opcional, `@slow`).

**Bloque**: 1.

#### D39 - Como se documenta una skill

**Propuesta**: docstring en `.py` + entrada en
`docs/SKILLS_LIBRARY.md`.
**Bloque**: 1.

#### D40 - Que pasa con las 65 microacciones de spec 08

**Propuesta**: se convierten en skills gradualmente. Las no
implementadas llevan `SKILL: false`.
**Bloque**: 1.

---

## 6. Bloques de construccion

19 bloques. Orden por dependencia real. Cada uno con objetivo,
entrada, salida, test, decisiones, estado.

### Bloque 0b - Infra on/off scaffold

**Objetivo**: que todo lo pesado de infra (Temporal, Supabase,
JWT/Auth, Docker, Redis) y todos los conectores esten detras de
feature flags. Default off. Contratos de infra no cambian con on/off.

**Entrada**: nada.

**Salida**:

- `infrastructure/config/feature_flags.py`.
- Env vars: `ENABLE_TEMPORAL`, `ENABLE_SUPABASE`, `ENABLE_JWT`,
  `ENABLE_OBS`, `ENABLE_<conector>`.
- `TemporalStub` que simula durabilidad sin Temporal.
- `SupabaseStub` (o Jsonl fallback) idem.
- `AuthStub` (single-user) idem.

**Test**: importar runtime con todos los flags off, ejecutar un
pipeline stub, activar Temporal on y verificar el mismo pipeline.

**Decisiones**: D23.

**Estado: DONE.

**Commits**: (vacio)

### Bloque 0 - Model Router Proxy

**Objetivo**: servicio interno que enruta a multiples LLMs
free-tier con fallback, cache y cuotas.

**Entrada**: 0b.

**Salida**:

- `interfaces/llm/router.py` con `ModelRouter`.
- `ModelRequest` / `ModelResponse`.
- Proveedores: Gemini, Groq, HuggingFace, Ollama.
- Cache de prompts identicos.
- Cuotas por tenant y dia.

**Test**: 2 proveedores mock, primer falla -> segundo responde.
Cache hit en prompt identico.

**Decisiones**: D22, D36.

**Estado: DONE.

### Bloque 1 - SkillSchema + biblioteca

**Objetivo**: definir SkillSchema completo y crear los primeros
10 skills reales (uno por departamento).

**Entrada**: 0b, 0.

**Salida**:

- `cognition/skills/schema.py` con `SkillSchema` y `SkillStep`.
- `cognition/skills/library/` con 10 skills reales.
- `docs/SKILLS_LIBRARY.md` autogenerado.

**Test**: instanciar skills de cada `mode`; rechazar invalidos.

**Decisiones**: D19, D20, D21, D37, D38, D39, D40.

**Estado**: PENDING.

### Bloque 2 - SkillRunner

**Objetivo**: ejecutor de skills paso a paso con validacion,
retry, timeout y persistencia intermedia.

**Entrada**: 1.

**Salida**:

- `orchestration/skill_runner.py` con `SkillRunner`.
- Soporte para los 5 `mode`.
- Idempotencia por `command_id` de skill.
- Persistencia intermedia para resume.

**Test**: skill de 3 pasos con fallo transitorio -> retry -> exito.
Skill con output invalido -> error.

**Decisiones**: ninguna pendiente.

**Estado**: PENDING.

### Bloque 3 - Prompt Composer

**Objetivo**: ensamblar prompt para pasos `mode="llm"` con contexto
de tenant, memoria, beliefs.

**Entrada**: 1, 2.

**Salida**:

- `interfaces/llm/composer.py` con `build_prompt()`.
- Variables tipadas desde `prompt_template`.
- Contexto del tenant aplicado.
- RAG con embeddings locales.

**Test**: dado un paso `mode="llm"`, el prompt resultante incluye
el contexto correcto.

**Decisiones**: D25.

**Estado**: PENDING.

### Bloque 5 - Trazabilidad real

**Objetivo**: `mission_id` propagado en todo. Endpoints reales.

**Entrada**: 2.

**Salida**:

- `mission_id` en `Event`.
- Persistencia de misiones (`data/tenants/<tid>/missions/`).
- `GET /api/missions` con lista real.
- `GET /api/missions/{id}/trace` con arbol.

**Test**: ejecutar mision -> reconstruir arbol completo.

**Decisiones**: D33.

**Estado**: PENDING.

### Bloque 0c - Laia <-> Runtime Bridge

**Objetivo**: Laia ve el runtime y explica al usuario sin bloquear.

**Entrada**: 5.

**Salida**:

- `interfaces/llm/laia.py` con `Laia`.
- Read-model `TenantRuntimeView`.
- Laia traduce eventos a lenguaje natural.
- Opcionalmente propone Intent.

**Test**: dado un evento `NodeDispatched`, Laia explica.

**Decisiones**: D29, D32, D35.

**Estado**: PENDING.

### Bloque 4 - Router real

**Objetivo**: router que lee catalogo de skills. Fallback en cascada.

**Entrada**: 1, 3.

**Salida**:

- `orchestration/interpreter.py`.
- Determinista + LLM-propuesto-validado.
- Resolucion de ambiguedad.

**Test**: mensaje "escribe a Juan" -> `Intent(write_email)`.

**Decisiones**: D31.

**Estado**: PENDING.

### Bloque 7 - Orquestador cableado

**Objetivo**: orquestador conectado al planner, scheduler y
SkillRunner. Ciclo cerrado.

**Entrada**: 2, 3, 4, 5.

**Salida**:

- `orchestration/orchestrator.py` cableado.
- Background worker (asyncio).
- `IntentQueue` + `IntentAggregator`.
- `SchemaAssembler`.
- Persistencia de misiones y aprobaciones.

**Test**: mensaje -> mission_id -> plan -> ejecucion -> traza.

**Decisiones**: D24, D30, D33, D34.

**Estado**: PENDING.

### Bloque 6 - Memoria real

**Objetivo**: CognitionStore cableado. MissionMemory persistida.

**Entrada**: 1, 5.

**Salida**:

- CognitionStore cableado a SkillRunner.
- MissionMemory persistida en tenant.
- Consolidacion working -> semantic.
- Busqueda semantica con embeddings.

**Test**: mission completada -> memoria coherente al reabrir.

**Decisiones**: D25.

**Estado**: PENDING.

### Bloque 8 - Agentes managers

**Objetivo**: 5 agentes con SOP, decisiones, QA, handoffs reales.

**Entrada**: 1, 2, 6.

**Salida**:

- Cada agente con `skills_allowed`, `sop`, `qa_rules`, `handoffs`.
- SOP ejecutado por Python.
- Decisiones evaluables.

**Test**: `CONTENT_AGENT` ejecuta SOP sobre brief -> articulo
validado.

**Decisiones**: ninguna pendiente.

**Estado**: PENDING.

### Bloque 0d - Tenant Compiler

**Objetivo**: dada raw data + ontologia, generar pipelines del
tenant.

**Entrada**: 1, 8.

**Salida**:

- `domains/compiler/` con `TenantCompiler`.
- Genera pipelines validos contra catalogo.
- Genera policies y capabilities.

**Test**: darle ontologia nueva -> pipelines validos.

**Decisiones**: ninguna pendiente.

**Estado**: PENDING.

### Bloque 9 - Tenants reales

**Objetivo**: 2 tenants con datos, knowledge, policy, credenciales.

**Entrada**: 6, 8, 0d.

**Salida**:

- `bor-agencia` con datos reales.
- `clinic-test` con datos reales.
- Policy afinada por tenant.
- Credenciales OAuth reales.

**Test**: cada tenant ve solo sus datos.

**Decisiones**: D27.

**Estado**: PENDING.

### Bloque 11 - Conectores reales

**Objetivo**: Drive, Gmail, Web Search, Calendar, Discord operativos.

**Entrada**: 2, 9.

**Salida**:

- Cada conector on/off.
- Rate limiting, circuit breaker, credential rotation.
- Webhooks inbound.

**Test**: enviar email real, recibirlo, traza completa.

**Decisiones**: D26.

**Estado**: PENDING.

### Bloque 13 - E2E real (acceptance)

**Objetivo**: test E2E con proveedores reales.

**Entrada**: 7, 9, 11.

**Salida**:

- Test E2E del vertical (apartado 7).
- Golden tests por skill.
- Tests de aislamiento entre tenants.

**Test**: el flujo del vertical corre end-to-end.

**Decisiones**: ninguna pendiente.

**Estado**: PENDING.

### Bloque 10 - Frontend Laia

**Objetivo**: UI con branch Laia <-> orquestador. Panel de misiones.

**Entrada**: 5, 7, 0c, 9.

**Salida**:

- Branch claro Laia / orquestador.
- Misiones reales via API.
- Aprobaciones en contexto.
- Wizard de tenant.

**Test**: un humano completa un flujo desde la UI.

**Decisiones**: ninguna pendiente.

**Estado**: PENDING.

### Bloque 12 - Observabilidad

**Objetivo**: metricas por skill/tenant/provider/LLM. Tracing.

**Entrada**: 5.

**Salida**:

- Logs estructurados JSON.
- Metricas Prometheus + Grafana free.
- Tracing OTel + Jaeger.

**Test**: dashboard accesible con datos reales.

**Decisiones**: D28.

**Estado**: PENDING.

### Bloque 14 - Infra production

**Objetivo**: docker-compose unificado, migraciones, secrets,
backups, deploy.

**Entrada**: 13 cerrado.

**Salida**:

- Docker-compose unificado.
- Migraciones Alembic.
- Secrets management.
- Deploy automatizado.

**Test**: bootstrap limpio -> sistema corriendo con 1 comando.

**Estado**: PENDING.

### Bloque 15 - Seguridad y compliance

**Objetivo**: prompt injection runtime, kill switch, rate limit,
auditoria, GDPR.

**Entrada**: 13 cerrado.

**Salida**:

- Prompt injection defense runtime.
- Kill switch global.
- Rate limiting por usuario/tenant.
- GDPR borrado/exportacion.

**Test**: intentos de bypass fallan.

**Estado**: PENDING.

---

## 7. Vertical slice (test de aceptacion)

No es un build. Es la prueba de que la infra sirve.

### 7.1 Setup

- 2 tenants: `bor-agencia` + `clinic-test`.
- 5 conectores: Drive, Gmail, Web Search, Calendar, Discord.
- N skills: minimo 10, una por departamento.

### 7.2 Flujo narrado

1. Llega un email a Gmail del tenant.
2. Runtime lo detecta.
3. Orquestador extrae Intent.
4. Construye TaskPlan.
5. `LEAD_GENERATION_AGENT` investiga al remitente (Web Search + Drive).
6. `DATA_ANALYSIS_AGENT` puntua el lead.
7. `CONTENT_AGENT` prepara borrador de respuesta.
8. `COMMUNICATION_AGENT` crea draft en Gmail (approval).
9. Calendar propone hueco para demo.
10. Discord notifica al humano.
11. Humano aprueba.
12. Sistema envia email + crea evento Calendar.
13. Todo trazado: mission -> plan -> nodes -> skills -> tools.
14. Laia explica al humano lo que ocurrio.

### 7.3 Criterios de exito

- El flujo corre con proveedores reales.
- La traza se reconstruye con un GET.
- Los 2 tenants estan aislados.
- Laia explica sin alucinar.
- Todo funciona con flags off.

---

## 8. Sistema on/off de infraestructura

| Componente | Default | Activacion | On | Off |
|---|---|---|---|---|
| Temporal | off | env `ENABLE_TEMPORAL` | durable workflows | single-process |
| Supabase | off | env `ENABLE_SUPABASE` | DB remota | JSONL local |
| JWT/Auth | off | env `ENABLE_JWT` | multi-user | usuario unico |
| Observabilidad | off | env `ENABLE_OBS` | tracing | logs locales |
| Redis | off | env `ENABLE_REDIS` | cache distribuida | cache local |
| Docker | off | env `ENABLE_DOCKER` | multi-servicio | proceso unico |
| Gmail | off | tenant config | real | stub |
| Drive | off | tenant config | real | cache local |
| Calendar | off | tenant config | real | stub |
| Discord | off | tenant config | real | stub |
| Web Search | on (gratis) | siempre | Brave/DuckDuckGo | (n/a) |

**Regla**: el codigo nunca sabe si algo esta on u off. Los contratos
son los mismos. Solo cambia la implementacion detras del flag.

---

## 9. Sistema de trabajo

### 9.1 Documento vivo

Este documento es la fuente. Cada bloque cerrado actualiza su entrada:
estado, commits.

### 9.2 Reglas

1. Un bloque a la vez. No se abre otro sin cerrar el actual o
   marcarlo BLOCKED con razon.
2. Antes de abrir un bloque, sus decisiones estan firmadas. Si no,
   sub-bloque de decision.
3. Cada bloque cierra con: codigo + test + commit + entrada
   actualizada.
4. Nada se commitea sin tests verdes.
5. Kernel -> PR separado + Kernel Boundary Rule.
6. Contradiccion spec-codigo -> Spec Contradiction Rule.
7. Nunca reabrimos una decision FIRMADA. Si hay que cambiarla,
   nueva decision que supersede con referencia.

### 9.3 Flujo por bloque

1. Yo propongo el bloque con sus decisiones.
2. Tu firmas o corriges.
3. Yo escribo codigo/tests/commits en bloques atomicos.
4. Tu ejecutas, me pasas output.
5. Si verde -> commit + push + actualizar plan.
6. Siguiente bloque.

---

## 10. Anti-repeat (4 tablas de tracking)

### 10.1 Tabla de decisiones

Vive en `docs/DECISIONS.md` (D01-D18 ya existen, D19+ se anaden).

### 10.2 Tabla de skills

Vive en `docs/SKILLS_LIBRARY.md` (nuevo, se crea en bloque 1).

| Skill ID | Department | Version | Estado | Bloque | Test |
|---|---|---|---|---|---|
| `communication.write_email` | communication | 1.0.0 | PENDING | 1 | - |
| `communication.read_email` | communication | 1.0.0 | PENDING | 1 | - |
| `communication.classify_email` | communication | 1.0.0 | PENDING | 1 | - |
| `research.web_search` | research | 1.0.0 | PENDING | 1 | - |
| `crm.create_contact` | crm | 1.0.0 | PENDING | 1 | - |
| `sales.score_lead` | sales | 1.0.0 | PENDING | 1 | - |
| `content.write_article` | content | 1.0.0 | PENDING | 1 | - |
| `analytics.generate_report` | analytics | 1.0.0 | PENDING | 1 | - |
| `social.create_post` | social | 1.0.0 | PENDING | 1 | - |
| `automation.schedule_job` | automation | 1.0.0 | PENDING | 1 | - |

### 10.3 Tabla de conectores

Vive en `docs/CONNECTORS_STATUS.md` (nuevo, se crea en bloque 11).

| Conector | Estado | Credenciales | Bloque | On/Off |
|---|---|---|---|---|
| Google Drive | stub | pendiente | 11 | off |
| Gmail | stub | pendiente | 11 | off |
| Google Calendar | stub | pendiente | 11 | off |
| Discord | no existe | pendiente | 11 | off |
| Web Search (Brave) | no existe | pendiente | 11 | on |

### 10.4 Tabla de bloques

Este documento, apartado 6.

---

## 11. Glosario y referencias

### 11.1 Glosario

- **Skill**: unidad atomica operativa, comunal, con prompt +
  few-shots + input/output schemas + steps.
- **SkillStep**: un paso de un skill, con un `mode` (tool, llm,
  validate, branch, handoff).
- **SkillRunner**: ejecutor de skills.
- **Agent**: manager de departamento, perfil Python + rol LLM
  limitado.
- **Intent**: propuesta del LLM, validada por el sistema.
- **TaskPlan**: DAG de nodos, construido por el planner.
- **TaskScheduler**: ejecutor topologico del plan.
- **Mission**: instancia de ejecucion completa.
- **MissionTrace**: arbol reconstruible desde el EventLog.
- **SchemaAssembler**: convierte texto LLM en schema pydantic.
- **ModelRouter**: enruta a multiples LLMs con fallback.
- **Laia**: capa PR, habla al usuario, no ejecuta.
- **Orchestrator**: Python, ensambla y dispone.
- **Tenant Compiler**: fabrica pipelines de tenants nuevos.
- **Feature flag**: on/off por env var.
- **Kernel Boundary Rule**: 5 condiciones para tocar kernel.
- **Spec Contradiction Rule**: si spec contradice codigo, se para.

### 11.2 Referencias

- docs/spec/00 - Principios del sistema.
- docs/spec/01-20 - Specs por tema.
- docs/DECISIONS.md - Decisiones firmadas.
- docs/STATUS.md - Estado del repo.
- docs/INVARIANTS.md - Invariantes del kernel.
- docs/audits/KERNEL_INVARIANTS.md - Audit cerrado.
- docs/AGENT_HANDOFF.md - Contexto para agentes.
- README.md - Vision general.

### 11.3 Como retomar el repo

Si eres un agente retomando este repo:

1. Lee `docs/STATUS.md` para saber donde esta el repo.
2. Lee este `docs/BUILD_PLAN.md` para saber donde va.
3. Lee `docs/DECISIONS.md` para saber que esta firmado.
4. Mira el apartado 6 de este plan para saber que bloque esta PENDING
   o IN_PROGRESS.
5. Sigue las reglas del apartado 9.
6. No inventes. No toques kernel sin Kernel Boundary Rule.
7. Cada commit con test verde.
```