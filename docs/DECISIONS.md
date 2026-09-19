# DECISIONS - Decisiones arquitectonicas cerradas

> Cada decision tiene UNA respuesta. No hay opciones. Si algo cambia,
> se abre una nueva Dxx y la anterior se marca SUPERSEDED.
>
> Estado global: FIRMADAS (C0.6 aprobado, 2026-09-18).
> (C0 aprobado 2026-09-18). C1 puede arrancar.
>
> Formato: RESPUESTA (la ley), LEY (donde queda escrita), CONSECUENCIA.

---

## D01 - Que pertenece al kernel vs. dominio

RESPUESTA: El kernel define tipos universales (Entity, Action, Context,
State, Policy, EventLog, Vocabulary). El dominio define kinds concretos
(agencia.lead, clinic.patient). El kernel NO conoce ningun kind de dominio.

LEY: docs/spec/00 + docs/INVARIANTS.md.

CONSECUENCIA: los 18 entity types de spec 03 son kernel (universales).
Las entidades de agencia/clinic/compiler son dominio.

---

## D02 - EntityCategory es metamodelo, no vocabulario

RESPUESTA: EntityCategory (actor, resource, tool, concept, event) define
categorias del metamodelo. NO es lo mismo que Vocabulary.entities (los
kinds concretos: actor, user, agent, tool, resource, goal, event).
Ambos coexisten con proposito distinto.

LEY: kernel/ontology/metamodel.py + kernel/ontology/vocabulary.py.

CONSECUENCIA: no se fusionan. Cada uno tiene su test.

---

## D03 - 18 entity types: ubicacion y namespace

RESPUESTA: viven en kernel/ontology/entities_catalog.py como BaseModel
frozen, extra=forbid. Namespace: core.* (core.person, core.company, ...)
para evitar colision con DEFAULT_VOCAB.

LEY: docs/spec/03 + kernel/ontology/entities_catalog.py (a crear en C1a).

CONSECUENCIA: EntityCategory sigue siendo metamodelo. Los 18 tipos son
kinds canonicos con prefijo core.

---

## D04 - 16 action verbs: ubicacion

RESPUESTA: viven en kernel/ontology/action_types.py como Literal +
FORBIDDEN_ACTION_ENTITY_PAIRS. Son verbos universales, no de dominio.

LEY: docs/spec/04 + kernel/ontology/action_types.py (a crear en C1b).

CONSECUENCIA: toda MicroActionSchema valida action_type in ActionType.

---

## D05 - MicroAction vs Capability vs Provider

RESPUESTA: tres niveles distintos:
- MicroAction (cognition/agents/microactions): comportamiento de negocio.
  Ej: sales.score_lead.
- Capability (connectors/core): capacidad tecnica. Ej: web.search.
- Provider (connectors/providers): implementacion. Ej: tavily.

LEY: docs/spec/08 (microacciones) + docs/spec/06 (tools).

CONSECUENCIA: una MicroAction declara la Capability que necesita, no al
Provider. El Provider lo elige ConnectorRouter.

---

## D06 - Donde viven las MicroActions

RESPUESTA: cognition/agents/microactions/<familia>.py. Cada familia es
un modulo. Un seed central las carga todas.

LEY: docs/spec/08.

CONSECUENCIA: C2 crea 15 modulos (uno por familia). Cada uno exporta
lista de MicroActionSchema.

---

## D07 - Donde viven las Capabilities

RESPUESTA: en connectors/core/capability_catalog.py derivadas de
connectors/providers/*.py. Se quedan donde estan. Congelado hasta C7.

LEY: connectors/core/capability_catalog.py.

CONSECUENCIA: capability_catalog.py NO debe importar
cognition.planning.internal_actions. La violacion de capas (import
actual) se resuelve moviendo internal_actions a cognition/planning/
puro, sin que connectors lo importe.

---

## D08 - Donde viven los Providers

RESPUESTA: en connectors/providers/*.py. Congelados como stubs hasta C7.

LEY: docs/spec/06.

CONSECUENCIA: ningun ciclo C1-C6 toca connectors/providers/.

---

## D09 - Quien puede crear TaskPlan

RESPUESTA: solo build_task_plan(intent, catalog) en
orchestration/planner.py. El LLM propone Intent. El planner determinista
construye TaskPlan. El LLM nunca emite TaskPlan directo.

LEY: docs/spec/11 + Spec Contradiction Rule.

CONSECUENCIA: si el LLM devuelve algo que parece un plan, se ignora.
Solo Intent -> planner -> TaskPlan.

---

## D10 - Formato TaskPlan -> TaskNode[] -> ejecucion

RESPUESTA: TaskPlan (frozen) contiene nodes: list[TaskNode]. TaskNode
(frozen) tiene id, agent_id, depends_on, state, input, output. El
scheduler ejecuta nodos con depends_on resueltas. Ciclos prohibidos
(validado al construir).

LEY: cognition/agents/schemas.py::TaskPlan + docs/spec/11.

CONSECUENCIA: C5a crea planner.py que produce TaskPlan valido. C5d
test E2E.

---

## D11 - Catalogo oficial de agentes: 5 (spec 10)

RESPUESTA: el catalogo son 5 agentes. Spec 10 es catalogo cerrado, no
generativo. Codigo tiene 2 (web_research, communication). Faltan 3
(lead_generation, data_analysis, content).

LEY: docs/spec/10.

CONSECUENCIA: C4 transcribe literal spec 10. No se inventan agentes.
La regla agents/ vs cognition/agents/ se resuelve en C4a:
cognition/agents/ es canonico. agents/ (base + registry) se queda
deprecated y se elimina en C7.

---

## D12 - Nombres canonicos de agentes

RESPUESTA: los nombres canonicos son los de spec 10, en MAYUSCULAS en
documentacion y snake_case en codigo. WEB_RESEARCH_AGENT ->
web_research_agent. La referencia RESEARCH_AGENT en spec 10 se
corrige a WEB_RESEARCH_AGENT en C0.4.

LEY: docs/spec/10 (actualizado en C0.4).

CONSECUENCIA: grep debe dar 0 ocurrencias de RESEARCH_AGENT fuera del
contexto WEB_RESEARCH_AGENT.

---

## D13 - Que puede proponer el LLM

RESPUESTA: el LLM propone Intent con:
- goal (str)
- kind (str, de una lista cerrada)
- entity_id (str)
- payload (dict, validado contra el schema del kind)
- rationale (str)
- confidence (float)

LEY: cognition/planning/intent.py + docs/spec/11.

CONSECUENCIA: cualquier Intent que no valide contra su schema se
descarta silenciosamente (fail-closed).

---

## D14 - Que NO puede proponer el LLM

RESPUESTA: el LLM NUNCA:
- Emite TaskPlan directo.
- Emite Handoff directo.
- Emite Action cruda (solo Intent).
- Ejecuta tools.
- Se auto-aprueba.
- Inventa kinds fuera del ACTION_CATALOG.

LEY: docs/spec/00 + Kernel Boundary Rule.

CONSECUENCIA: guardrails.py debe rechazar output que contenga patrones
de ejecucion. Tests en tests/llm/test_guardrails.py.

---

## D15 - Kernel Boundary Rule (alcance)

RESPUESTA: kernel/ se modifica solo si CUMPLE LAS CINCO (ver
docs/spec/00). Toda modificacion en PR separado + tests kernel verdes
antes/despues + test_no_kernel_imports_domains verde.

LEY: docs/spec/00_SYSTEM_PRINCIPLES.md.

CONSECUENCIA: los ciclos C1, C2, C5 anaden a kernel sin mutar. Cualquier
mutacion se justifica caso por caso en el commit.

---

## D16 - Spec Contradiction Rule

RESPUESTA: si dos specs se contradicen, o una spec contradice el codigo
sin decision cerrada, la implementacion se detiene. Se abre decision,
se actualiza spec, se implementa.

LEY: docs/spec/00_SYSTEM_PRINCIPLES.md.

CONSECUENCIA: el agente que escribe codigo NO resuelve contradicciones
implicitamente. Casos conocidos (RESEARCH_AGENT, refs rotas de spec 09,
spec 08 incompleta) se resuelven en C0.4.

---

## D17 - [SUPERSEDED por D18] contracts.execution.Action vs execution.action.Action

RESPUESTA: contracts/execution.Action es el canonico (frozen, extra=forbid,
tenant_id obligatorio, ActionParams tipado). execution/action.Action y
execution/result.ExecutionResult se marcan deprecated y se eliminan en C7.

El Executor migra a aceptar Action o str (retrocompatible). El camino
legacy execute_action() se elimina en C7.

LEY: docs/spec/07 + docs/spec/00 (Pydantic como sistema de tipos).

CONSECUENCIA:
- Sin esto, C1e valida contra el contrato que NO manda (el laxo).
- Requiere refactor de execution/executor.py: firma execute(action: Action|str).
- Requiere tests nuevos en tests/execution/test_executor_action_contract.py.
- BLOQUEA C1e. Si D17 no se firma en C0.6, C1e se pospone a C2.

---

## D18 - contracts.execution.Action es descriptor de auditoria, no input ejecutable

RESPUESTA: Supersede D17. La distincion real es:
- contracts.execution.Action / ActionParams (values: Dict[str, str]):
  DESCRIPTOR DE AUDITORIA. Resume tipos ("<str>", "<int>"), no valores.
  Su destino es el EventLog, no el Executor.
- execution.action.Action y Executor.execute(action: str, params: dict):
  CAMINO DE EJECUCION CANONICO. Recibe valores reales.
- Executor.execute_action() queda DEPRECATED (nadie lo llama en src/).

LEY: contratos en contracts/execution.py + execution/executor.py.

CONSECUENCIA:
- C1e valida contra el camino real (str + params) y NO contra el descriptor.
- execute_action() emite DeprecationWarning y se elimina en C7.
- No se migra el Executor a aceptar Action: seria un error semantico
  (el descriptor no lleva datos para ejecutar).
- Cierra AUD-15 sin incoherencia.

## D23 - Bloque de arranque

RESPUESTA: arrancamos por bloque 0b (infra on/off scaffold), no por
bloque 1 (Skill). Razon: sin on/off, cada bloque posterior arrastra
decisiones de infra y hay que reabrirlas.

LEY: docs/BUILD_PLAN.md apartado 6, bloque 0b.

CONSECUENCIA:
- Primer bloque a construir: 0b.
- Antes de abrirlo, D23 queda FIRMADA.
- Bloque 1 (Skill) arranca despues de 0b.
- El resto de decisiones D19-D22, D24-D40 se firman al abrir su bloque.

FIRMADA: 2026-09-18.

---

## Como se mantiene este documento
1. Cada decision tiene una entrada. No se borra. Se supersede.
2. Las entradas estan FIRMADAS desde 2026-09-18 (C0.6).
3. Si algo cambia, se abre Dxx+1 y Dxx se marca SUPERSEDED.
4. Las decisiones nuevas van al final, no se reordenan.


---

## D19 - Estructura de un Skill

RESPUESTA: prompt + few-shots + input/output schemas + steps + tool_id + validacion + postcond + tenant_overrides + department + cost_hint.
Prompt como string con `{variable}`. Few-shots como lista de dicts `{input, output}`.
LEY: `cognition/skills/schema.py` (a crear en Bloque 1).
CONSECUENCIA: SkillSchema es el contrato del skill; el LLM no lo modifica en runtime.

## D20 - Idioma de prompts

RESPUESTA: base en ingles, overrides por tenant en su idioma.
LEY: `cognition/skills/schema.py` + `interfaces/llm/composer.py` (Bloque 3).
CONSECUENCIA: el prompt base es estable; la localizacion vive en tenant_overrides.

## D21 - Versionado de skills

RESPUESTA: global + overrides. El tenant cambia prompt/tono/restricciones, NO la estructura de pasos.
LEY: `cognition/skills/schema.py`.
CONSECUENCIA: la estructura del skill es invariante; los overrides son cosmeticos/comportamentales, no estructurales.

## D22 - Model router: proveedores free-tier

RESPUESTA: 5 proveedores, en este orden de preferencia:
- Gemini 3.6 Flash (Google, free tier generoso).
- Groq (Llama 3.3 70B, free tier rapido).
- XAI / Grok (xAI, OpenAI-compatible).
- OpenRouter (gateway a multiples modelos).
- Hugging Face Inference API (fallback).

Enrutado por preferred_model > cost_hint > orden natural. Fallback en
cascada con cache en memoria de prompts identicos.

LEY: `interfaces/llm/router.py` (Bloque 0, ya implementado).

CONSECUENCIA: los modelos concretos se cambian por env var
(`GEMINI_MODEL`, `GROQ_MODEL`, etc.) sin tocar codigo.

## D24 - Worker de misiones

RESPUESTA: asyncio para misiones (concurrencia por tenant).
APScheduler para schedules declarados por tenant. Temporal on/off
para production.

LEY: `orchestration/orchestrator.py` + `orchestration/scheduler.py`
(Bloque 7).

CONSECUENCIA: sin Temporal, las misiones corren en el mismo proceso.
Cuando se active Temporal, el contrato no cambia.

## D25 - Embeddings para memoria

RESPUESTA: local con `sentence-transformers`. Si el rendimiento no
llega en produccion, se cambia a API con on/off por env var.

LEY: `cognition/memory/` + `interfaces/llm/composer.py`
(Bloques 3 y 6).

CONSECUENCIA: privacidad por defecto; sin llamadas externas para
embeddings.

## D26 - Web Search proveedor

RESPUESTA: Brave Search API (free tier) como principal. Fallback a
DuckDuckGo (sin API key) cuando se agota la cuota.

LEY: `connectors/providers/catalog_ai_web.py` + tool `web_search`
(Bloque 11).

CONSECUENCIA: el conector se declara on/off; sin credenciales
degrada a DuckDuckGo.

## D27 - Los 2 tenants del vertical

RESPUESTA:
- `bor-agencia` (ya existe, dominio agencia, caso real).
- `clinic-test` (nuevo, dominio clinic, para probar compilador).

LEY: `data/tenants/` + `domains/agencia/` + `domains/clinic/`
(Bloque 9).

CONSECUENCIA: el vertical slice usa estos 2. Cualquier otro tenant
es extra.

## D28 - Observabilidad

RESPUESTA:
- Logs: estructurados JSON con `structlog` a stdout.
- Metricas: Prometheus + Grafana Cloud free tier.
- Tracing: OpenTelemetry SDK + Jaeger local.

LEY: `infrastructure/telemetry/` (Bloque 12).

CONSECUENCIA: todo gratis por defecto; migrable a stack de pago sin
cambiar contratos.

## D29 - Laia: polling o subscribe

RESPUESTA: read-model persistido (JSON o Redis) + Laia hace polling
ligero cada N segundos. WebSocket en production.

LEY: `interfaces/llm/laia.py` (Bloque 0c).

CONSECUENCIA: sin WebSocket, la UI de misiones actualiza por polling.
Cuando se active WebSocket, mismo read-model.

## D30 - SchemaAssembler

RESPUESTA:
1. LLM llamado con `response_schema` (structured output nativo de
   Gemini / Groq / OpenRouter).
2. Si el proveedor no soporta structured output: prompt + parseo
   JSON.
3. Output pasa por `pydantic.validate_json()` contra el schema
   declarado.
4. Si no valida: 1 reintento con feedback del error.
5. Si sigue sin validar: `ValidationFailed`.

LEY: `orchestration/orchestrator.py` (Bloque 7).

CONSECUENCIA: nunca se propaga un output que no cumple schema.

## D31 - Que pasa si no existe skill

RESPUESTA: router devuelve `NoSkillFound`. Laia lo comunica. No se inventa skill en runtime.
LEY: `orchestration/interpreter.py` (Bloque 4).
CONSECUENCIA: fail-closed: sin skill declarada, no hay ejecucion.

## D32 - Laia propone Intent?

RESPUESTA: si, solo via `Intent`. Laia nunca ejecuta.
LEY: `interfaces/llm/laia.py` (Bloque 0c).
CONSECUENCIA: Laia solo propone; Policy + Executor deciden.

## D33 - Acumulacion de intents -> task list

RESPUESTA: IntentQueue en `data/tenants/<tid>/intents.jsonl`. IntentAggregator agrupa por afinidad. TaskScheduler consume planes.
LEY: `orchestration/orchestrator.py` (Bloque 7).
CONSECUENCIA: intents persistidos; el scheduler consume planes agregados.

## D34 - Foto como trigger

RESPUESTA: `photo_received` -> Vision LLM (Gemini Vision o GPT-4V) -> texto + intent -> mismo validador.
LEY: `interfaces/llm/` + `execution/tools/` (Bloques 7 + 11).
CONSECUENCIA: vision es un trigger mas; mismo contrato de Intent.

## D35 - Como Laia ve el runtime

RESPUESTA: read-model `TenantRuntimeView` con misiones activas, aprobaciones pendientes, ultimos eventos, metricas resumidas.
LEY: `interfaces/llm/laia.py` (Bloque 0c).
CONSECUENCIA: Laia lee; no escribe estado de runtime.

## D36 - Modelo preferido por agente vs skill

RESPUESTA: 1) Paso declara `preferred_model` -> ese. 2) Skill declara `preferred_model` -> ese. 3) Agente declara `preferred_model` -> ese. 4) ModelRouter decide por `cost_hint` y disponibilidad.
LEY: `interfaces/llm/router.py` (Bloque 0).
CONSECUENCIA: jerarquia determinista; el router solo decide lo no declarado.

## D37 - Skills como codigo o como datos

RESPUESTA: `.py` para el repo. YAML solo si un tenant necesita declarar skills sin tocar codigo.
LEY: `cognition/skills/` (Bloque 1).
CONSECUENCIA: skills del repo en Python; YAML es via de escape para tenants.

## D38 - Como se testea una skill

RESPUESTA: test unitario input + output + pasos `tool` con mocks + pasos `llm` con stub determinista + golden test opcional `@slow`.
LEY: `tests/skills/` (Bloque 1).
CONSECUENCIA: toda skill nueva exige los 4 niveles de test.

## D39 - Como se documenta una skill

RESPUESTA: docstring en `.py` + entrada autogenerada en `docs/SKILLS_LIBRARY.md`.
LEY: `docs/SKILLS_LIBRARY.md` (Bloque 1).
CONSECUENCIA: la biblioteca se autogenera; no se escribe a mano.

## D40 - Que pasa con las 65 microacciones de spec 08

RESPUESTA: se convierten en skills gradualmente. Las no implementadas llevan flag `SKILL: false`.
LEY: `cognition/skills/` (Bloque 1).
CONSECUENCIA: migracion incremental; sin big-bang.
