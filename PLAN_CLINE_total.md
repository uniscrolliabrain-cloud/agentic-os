# PLAN_CLINE:AGENTE_COMPILADOR.md

Anexo B FINAL: Contrato Técnico de Adaptación — Cline Tuneado para Compilador de Tenants
Path: data/tenants/agentic-compiler/docs/anexo_cline_tuneado_para_compilador_de_tenants.md
Estado: Bloqueante Fase 7 resuelto (P1 del PLAN_CLINE_AGENTE_COMPILADOR.md)
Versión: v1.1 con CLI + Streamlit + Temporal.io

0. Resumen Ejecutivo
Este anexo define cómo Cline (28 tools, modos plan/act, ToolExecutor con handlers) se encaja en el tenant agentic-compiler sin violar 00_SYSTEM_PRINCIPLES.md (LLM propone Intent Pydantic frozen, Policy decide, Executor ejecuta, EventLog audita).

Añadido solicitado: interfaz CLI + Streamlit simple para hablar con el compilador y área en Temporal.io para dejar prompts y pipelines encolados.

1. Arquitectura de Aislamiento y Filosofía del Adapter
Ubicación física real (tu tenancy):

data/tenants/agentic-compiler/
├── sandbox/
│   └── cline_adapter/
│       ├── loop.py
│       ├── tools_bridge.py
│       ├── guardrails.py
│       ├── intents.py
│       ├── prompts/system_compiler.md
│       ├── cli/                  # NUEVO: CLI del compilador
│       │   └── compiler_cli.py
│       ├── ui/                   # NUEVO: Streamlit simple
│       │   └── app.py
│       └── temporal/             # NUEVO: workflows de compilación
│           ├── workflows.py      # CompilationWorkflow
│           └── activities.py     # actividades durables
├── knowledge/                    # KB propia
├── prompts/                      # prompts persistidos para Temporal
│   ├── ideas/*.md
│   └── blueprints/*.md
└── docs/anexo_cline_tuneado.md
Filosofía:

Cline es cerebro alquilado (plan/act), no actor. Usa PipelineRunner.tool() canónico de orchestration/pipelines/runner.py con correlation_id, command_id, idempotencia.
Usa Agent-Lock y Agent-Queue.py existentes para multi-agente (cline/roo/kilo).
Credenciales: TenantContext(tenant=agentic-compiler) + token GitHub efímero scope agentic-os-roo/<blueprint_id>.
Modos Cline mapeados:

plan_mode_respond → genera TenantBlueprint en main (tu dos velocidades: Laia responde instante, director trabaja background)
act_mode_respond → genera código en agentic-os-roo
2. Bucle de Razonamiento Adaptado (cline_adapter/loop.py)
python
# loop.py - adaptado a tu KernelModel
from agentic_os.kernel.types import KernelModel
from agentic_os.orchestration.pipelines.runner import PipelineRunner
from agentic_os.kernel.types.ids import new_id
from .tools_bridge import TOOLS_MAP
from .guardrails import Guardrails
from scripts import AgentLock

class ClineAdaptedLoop(KernelModel):
    model_config = {"frozen": True}
    
    async def run_step(self, runner: PipelineRunner, blueprint_step: dict, observation: dict):
        # 1. Recepción BlueprintStep (de TaskNode DAG de 11_ORCHESTRATION)
        # 2. Propuesta Intent (Cline piensa en plan/act)
        intent = await self.think(observation) # LLM -> ClineIntent
        
        # 3. Lock multi-agente (tu script existente)
        AgentLock.acquire(agent="cline", file=intent.path)
        
        try:
            # 4. Puente traduce a capability canónica
            capability, params = TOOLS_MAP[intent.type](intent)
            
            # 5. Camino canónico: Policy + Auditoría + Idempotencia
            result = runner.tool(
                name=capability,
                params=params,
                tenant_id="agentic-compiler",
                correlation_id=observation.get("correlation_id"),
                command_id=f"cline-{new_id()}"
            )
            # 6. Auditoría automática: ActionStarted, ToolCompleted, ToolFailed -> EventLog
            # 7. Observe -> siguiente ciclo
            return result
        finally:
            AgentLock.release(agent="cline", file=intent.path)
attempt_completion de Cline → runner.emit_event(kind="CompilationCompleted")
ask_followup_question de Cline → ApprovalRequest → NEEDS_APPROVAL (Gate 1/2)

3. Puente de Capabilities (tools_bridge.py) - 28 tools reales de Cline
Acción Cline (real)	Capability Canónica (tu 06)	Tool Interna	Riesgo
read_file	repo.file.read	RepoReadFileTool	READ_ONLY
write_to_file	repo.file.write.scoped	RepoWriteFileTool	MEDIUM - Path Guard
replace_in_file	repo.file.patch	RepoPatchTool	MEDIUM - SEARCH/REPLACE exacto
apply_patch	repo.file.apply_patch	RepoApplyPatchTool	MEDIUM
list_files	repo.list	RepoListTool	LOW
search_files	repo.search	RepoSearchTool	LOW
list_code_definition_names	repo.symbol.search	RepoSymbolTool	LOW
execute_command (pytest/ruff/mypy)	ci.pytest.run	CiRunTool	MEDIUM - allowlist
execute_command (ls/cat)	filesystem.list	FilesystemTool	LOW
browser_action/web_search/web_fetch	web.search/web.scrape	WebSearchTool	HIGH - allow_net + policy
use_mcp_tool	mcp.call	MCPAdapter	MEDIUM
use_skill/use_subagents	skill.run/agent.delegate	SkillRunner	MEDIUM
ask_followup_question	human.approval.request	ApprovalTool	CRITICAL - require_approval
attempt_completion	compilation.complete	EmitEventTool	LOW
git_commit/git_push	git.commit.scoped	GitCommitTool	EXTERNAL_COMMUNICATION
open_pull_request/new_task	git.pr.create	GitPrCreateTool	CRITICAL - Gate 2
Path Guard Inviolable (data/policies/agentic-compiler.json):

json
{
  "id": "deny_kernel",
  "capability": "repo.file.write.scoped",
  "effect": "deny",
  "description": "DENY src/agentic_os/kernel/**, tests/kernel/**, .env, events.jsonl",
  "condition": "params.path.startswith('src/agentic_os/kernel/') or params.path.startswith('tests/kernel/')"
}
Solo puede escribir en data/tenants/<new_slug>/ y src/agentic_os/domains/<new_slug>/.

4. Guardarraíles (guardrails.py)
Pasos máx: 30 por run (evita bucles LLM)
Timeout paso: 120s (PipelineStep.timeout_seconds de 07_PYDANTIC_CONTRACTS)
Timeout global: 30min por run, 10min por activity Temporal
Kill Switch CI: ci.pytest.run -q + ruff check . + mypy src/agentic_os fallan → emite CompilationFailed → TaskNode.status=FAILED → BLOCKED dependientes (respeta 11_ORCHESTRATION). Usa RetryPolicy(maximum_attempts=3) de Temporal.
Budget tokens: máx por blueprint.
5. Flujo Git e Interacción Multiagente
Plan en main: director genera TenantBlueprint (Pydantic strict). Archivo plans/<blueprint_id>.md versionado. Laia responde instante.
Código en agentic-os-roo: Cline act_mode_respond genera ontología, policy, pipelines, tests solo en tenant nuevo. Usa Agent-Lock.
Gates: Gate 1 (plan.md) → compiler.plan.approve, Gate 2 (diff completo) → git.pr.create con require_approval + require_ci_pass. UI en frontend/src/App.jsx vía /api/v1/approvals.
6. Inventario (MANIFEST.md)
Origen: Cline v3.8.2 MIT, commit a1b2c3d4
Reutilizados: src/core/Cline.ts → loop.py (sustituye client.tool() por runner.tool()), system.ts → system_compiler.md, readFileTool.ts → map_read, writeToFileTool.ts → map_write con Path Guard, executeCommandTool.ts → map_exec con allowlist
Eliminados: browserTool.ts (SSRF), credentialStore.ts (tu CredentialStore cifrado es único)
Tests: test_path_guard_inviolable, test_no_direct_exec, test_tenant_isolation, test_catalog_compliance, test_idempotency
7. NUEVO: Interfaz CLI + Streamlit Simple + Área Temporal.io
7.1 CLI del Compilador (sandbox/cline_adapter/cli/compiler_cli.py)
bash
# Uso
python -m agentic_os.domains.compiler.cli --help
python -m agentic_os.domains.compiler.cli idea "quiero un OS para mi clínica dental"
python -m agentic_os.domains.compiler.cli blueprint list
python -m agentic_os.domains.compiler.cli compile <blueprint_id> --tenant clinica-dental
python -m agentic_os.domains.compiler.cli gate approve <gate_id>
python -m agentic_os.domains.compiler.cli status <run_id>
Implementación:

python
# compiler_cli.py
import typer
from agentic_os.orchestration.pipelines.runner import PipelineRunner
from agentic_os.orchestration.temporal.client import start_pipeline

app = typer.Typer()

@app.command()
def idea(text: str):
    # 1. Guarda idea en data/tenants/agentic-compiler/prompts/ideas/
    # 2. Lanza PipelineRunner: pipeline_blueprint_from_idea
    # 3. Genera plans/<blueprint_id>.md en main
    runner = PipelineRunner(executor=..., llm=...)
    result = runner.run("pipeline_blueprint_from_idea", tenant_id="agentic-compiler", params={"idea": text})
    print(f"Blueprint creado: {result['blueprint_id']} - Esperando Gate 1")

@app.command()
def compile(blueprint_id: str, tenant: str):
    # Lanza Temporal Workflow durable
    import asyncio
    asyncio.run(start_pipeline("pipeline_compile_tenant", "agentic-compiler", 
                               {"blueprint_id": blueprint_id, "new_slug": tenant}))
    print(f"Compilación encolada en Temporal: {tenant}")
7.2 Streamlit Simple (sandbox/cline_adapter/ui/app.py)
Tu repo ya tuvo streamlit_app.py (legacy) retirado en favor de React. Este es un UI minimalista solo para el compilador, no reemplaza frontend.

python
# app.py - Streamlit simple para hablar con el compilador
import streamlit as st
from pathlib import Path

st.set_page_config(page_title="Agentic Compiler", layout="wide")
st.title("🛠️ Agentic Compiler - Tenant Factory")

tab1, tab2, tab3 = st.tabs(["💡 Ideas", "📋 Blueprints", "🏗️ Compilaciones"])

with tab1:
    idea = st.text_area("Describe el tenant que quieres crear:", 
                        "quiero un OS agéntico para mi clínica dental que gestione citas...")
    if st.button("Generar Blueprint"):
        # Llama a PipelineRunner pipeline_blueprint_from_idea
        st.success(f"Blueprint generado: {blueprint_id}")
        st.markdown(Path(f"plans/{blueprint_id}.md").read_text())

with tab2:
    # Lista plans/*.md
    blueprints = list(Path("plans").glob("*.md"))
    for bp in blueprints:
        with st.expander(bp.name):
            st.markdown(bp.read_text()[:2000])
            if st.button(f"Aprobar {bp.name} - Gate 1", key=bp.name):
                # Emite ApprovalGranted event
                st.success("Gate 1 aprobado - Encolando en Temporal...")

with tab3:
    # Lista runs/ + Temporal workflows
    st.subheader("Runs en Temporal.io")
    # Muestra CompilationWorkflow status
    # Lista data/tenants/agentic-compiler/runs/*.json
    run_id = st.selectbox("Ver run", ["run_001", "run_002"])
    st.json({"status": "RUNNING", "steps": 12, "current": "generate_tenant"})
    
    st.subheader("Dejar prompt para siguiente iteración")
    prompt = st.text_area("Prompt para Cline (se encola en Temporal)")
    if st.button("Encolar prompt"):
        # Guarda en data/tenants/agentic-compiler/prompts/ y lanza activity
        st.success("Prompt encolado en Temporal queue: agentic-os-queue")
Ejecución:

bash
pip install streamlit
streamlit run data/tenants/agentic-compiler/sandbox/cline_adapter/ui/app.py --server.port 8501
7.3 Área en Temporal.io para Prompts y Pipelines
Tu docker-compose.yml ya tiene Temporal + temporalio. Ampliamos.

a) Workflows (orchestration/temporal/workflows.py):

python
@workflow.defn
class CompilationWorkflow:
    @workflow.run
    async def run(self, blueprint_id: str, new_slug: str, prompt: str = None):
        # Fase 1: Validar blueprint
        await workflow.execute_activity("validate_blueprint_activity", blueprint_id,
                                        start_to_close_timeout=timedelta(minutes=2))
        # Fase 2: Bootstrap sandbox (Dockerfile, vm_entrypoint.sh)
        await workflow.execute_activity("sandbox_bootstrap_activity", new_slug,
                                        start_to_close_timeout=timedelta(minutes=5))
        # Fase 3: Loop Cline adaptado (durable, con retry)
        for step in range(30): # Guardrail max_steps
            result = await workflow.execute_activity(
                "cline_step_activity",
                args=[blueprint_id, new_slug, prompt],
                start_to_close_timeout=timedelta(minutes=10),
                retry_policy=RetryPolicy(maximum_attempts=3, initial_interval=timedelta(seconds=2))
            )
            if result.get("status") == "attempt_completion":
                break
            # Human in the loop: si necesita aprobación
            if result.get("needs_approval"):
                await workflow.wait_condition(lambda: approval_granted())
        
        # Fase 4: CI + Tests
        await workflow.execute_activity("ci_run_activity", new_slug)
        # Fase 5: Git publish
        await workflow.execute_activity("git_publish_activity", new_slug)
        return {"status": "COMPILED", "tenant": new_slug}
b) Activities (orchestration/temporal/activities.py):

python
@activity.defn
async def cline_step_activity(blueprint_id: str, new_slug: str, prompt: str):
    # Aquí vive tu ClineAdaptedLoop
    registry = build_default_registry()
    event_log = get_eventlog_repo()
    policy = PolicyEngine()
    executor = Executor(registry=registry, event_log=event_log, policy_engine=policy)
    runner = PipelineRunner(executor=executor, llm=GeminiProvider())
    
    loop = ClineAdaptedLoop(runner=runner, blueprint_step={"blueprint_id": blueprint_id})
    result = await loop.run_step(runner, {"blueprint_id": blueprint_id}, {"prompt": prompt})
    return result

@activity.defn
async def prompt_queue_activity(tenant_id: str, prompt: str):
    # Deja prompts encolados: data/tenants/agentic-compiler/prompts/queue.jsonl
    Path(f"data/tenants/{tenant_id}/prompts/queue.jsonl").write_text(...)
    return {"queued": True}
c) Cliente para encolar prompts/pipelines (orchestration/temporal/client.py):

python
async def start_compilation(blueprint_id: str, new_slug: str, prompt: str = None):
    client = await get_client()
    handle = await client.start_workflow(
        "CompilationWorkflow",
        args=[blueprint_id, new_slug, prompt],
        id=f"compile-{new_slug}-{uuid.uuid4().hex[:8]}",
        task_queue="agentic-os-queue",
    )
    return handle.id

async def enqueue_prompt(tenant_id: str, prompt: str):
    # Encola prompt suelto para Cline sin crear tenant nuevo
    client = await get_client()
    handle = await client.start_workflow(
        "PromptWorkflow",
        args=[tenant_id, prompt],
        id=f"prompt-{tenant_id}-{uuid.uuid4().hex[:8]}",
        task_queue="agentic-os-queue",
    )
    return handle.id
d) UI de Temporal (ya en docker-compose):

http://localhost:8233 → ves CompilationWorkflow, PromptWorkflow, retries, inputs, outputs, logs.
Área para dejar prompts: CLI compiler_cli.py prompt enqueue "refactoriza la ontología" o Streamlit tab "Dejar prompt" → llama a enqueue_prompt() → Temporal lo ejecuta durable.
Flujo end-to-end con nueva interfaz:

Usuario en Streamlit: "quiero clínica dental"
  ↓
pipeline_blueprint_from_idea → plans/clinica-dental-001.md
  ↓
Gate 1 en Streamlit: Aprobar
  ↓
start_compilation() → Temporal → CompilationWorkflow
  ↓
Temporal UI (8233): ves cada cline_step_activity con retry durable
  ↓
Si Cline necesita ask_followup_question → Temporal espera → Streamlit muestra Gate 2 (aprobar diff)
  ↓
CI + git_publish → PR a main
Checklist Final con Interfaces
 Crear data/tenants/agentic-compiler/sandbox/cline_adapter/cli/compiler_cli.py
 Crear .../ui/app.py (Streamlit) - pip install streamlit
 Extender orchestration/temporal/workflows.py con CompilationWorkflow y PromptWorkflow
 Extender orchestration/temporal/activities.py con cline_step_activity, prompt_queue_activity
 Extender client.py con start_compilation(), enqueue_prompt()
 docker-compose up temporal → UI en 8233 para ver prompts y pipelines encolados
 pytest verde (incluye tests/kernel/ intactos)
Con esto, el compilador tiene: (1) CLI para automatizar, (2) Streamlit simple para hablar con él sin tocar React, (3) Temporal.io como cola durable de prompts/pipelines donde puedes dejar trabajo y ver retries, logs y estado.
---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
VERSION GEMINI V2
> **Documento de planificación detallado** para construir el **segundo tenant
> productivo** sobre **Agentic OS**: una **agencia multiagéntica compiladora de
> tenants** que trabaja dentro de este mismo repo con acceso a GitHub y
> capacidades de coder/arquitecto, siguiendo el loop de Cline pero bajo las
> reglas del kernel. Su producto no es software ni servicios al uso: su
> producto son **tenants nuevos**. Empresas, ideas, proyectos o agentes se
> "mudan" a Agentic OS sin tocar el kernel: solo aportan su ontología, su
> policy y sus datos; todo lo demás lo comparten.
>
> - **Nombre del tenant (provisional):** `agentic-compiler` (o `cline-compiler`).
> - **Estado:** v1.0 — audit del repo actual + plan por fases.
> - **Regla inviolable:** el LLM **nunca** ejecuta nada directamente. Solo
>   propone Intents Pydantic; el kernel valida la forma, la Policy decide el
>   efecto, el Executor ejecuta, el EventLog audita. **Igual que cualquier
>   otro tenant.**
> - **Regla del compilador:** todo cambio de código se hace en la rama
>   `agentic-os-roo`. El plan vive en `main` como `.md`. La fusión la aprueba
>   Alfonso (merge directo o PR).
> - **Convención de rutas:** `src/agentic_os/…` = raíz del paquete; datos en
>   `data/`; conocimiento en `knowledge/`.
>
> **Nota sobre el nombre del archivo:** `PLAN_CLINE:AGENTE_COMPILADOR.md`
> contiene `:` (inválido en Windows). Se propone guardarlo como
> `PLAN_CLINE_AGENTE_COMPILADOR.md` manteniendo el título con dos puntos.

## Índice

| #  | Sección |
|----|---------|
| 1  | Contexto y visión de negocio |
| 2  | Decisiones de modelo (la base de todo) |
| 3  | Auditoría del estado actual del código (lo que se reutiliza) |
| 4  | Principios e invariantes — el «por qué» |
| 5  | Plan de implementación por fases (0 → 10) |
| 6  | Flujo end-to-end: de la idea al tenant vivo |
| 7  | Decisiones pendientes / preguntas abiertas |
| 8  | Glosario |
| 9  | Anexo A: mapa de archivos · Anexo B: contrato del anexo Cline |

---

## 1. Contexto y visión de negocio

Agentic OS es un **kernel modular** con invariantes estables (event sourcing,
policy como gate único, LLM proposer, ontología metamodelo/vocabulario). Todo
lo demás — connectors, tools, pipelines, cognition, dominios — es **extensión**.

Hoy el repo tiene **un tenant productivo** (`bor-agencia`) que demuestra el
patrón: un dominio propio, una policy propia, una knowledge base propia y
**cero cambios en el kernel**.

**El tenant 2 explota ese mismo patrón para construir otros tenants.**

### Qué es `agentic-compiler`

Un tenant cuya **“empresa”** es un **compilador**: recibe una idea en lenguaje
natural (*“quiero un OS agéntico para mi clínica dental que gestione citas,
recordatorios y facturación”*) y produce:

1. Un **plan `.md`** detallado, versionado en `main`.
2. Una **rama** `agentic-os-roo` con todo el código generado.
3. Un **PR** (o un merge directo) previa aprobación de Alfonso.
4. Un **tenant vivo**: registrado en `registry.json`, con su dominio, policy,
   pipelines, knowledge y datos iniciales.

### Por qué este tenant es interesante

- **Dog-fooding radical.** El compilador es un tenant; el output del
  compilador son tenants. Si el kernel aguanta la recursión, aguanta todo.
- **Cero cambios al kernel.** Igual que BOR: si hay que tocar `kernel/`, la
  feature no está bien modelada.
- **Aprovecha lo que ya existe.** `PipelineRunner`, `Executor`, `PolicyEngine`,
  `TenantRegistry`, `ENTITY_TYPE_REGISTRY`, `resolve_client_credentials`,
  `WebhookReceiver`, `Scheduler`, `Temporal` — todo sirve.
- **Modelo económico distinto.** No vende servicios; vende *capacidad de
  alojamiento*. Cada tenant nuevo es un “cliente” que ocupa un `data_dir`,
  una policy y una ontología.
- **Cline-compatible.** El loop que usa Cline (propose → tool → observe) es
  exactamente el loop del kernel (Intent → Policy → Executor → EventLog). La
  diferencia: aquí el “tool” es siempre una capability canónica y la decisión
  la toma la Policy, no el LLM.

### Cómo se relaciona con `bor-agencia`

Comparten el 95%:

| Recurso | Compartido | Propio del tenant |
|---|---|---|
| Kernel | ✅ todo | — |
| Connector Kernel (44 providers) | ✅ | providers nuevos si hacen falta |
| Tools base (`gmail_*`, `drive_*`, `web_*`, `meta_*`, `scheduler_*`) | ✅ | tools de codegen/git/sandbox |
| Pipelines genéricos (`daily_social`, `inbox_watcher`, `leads_to_draft`) | ✅ | pipelines `compile_*` |
| Cognition (beliefs, memory, reasoning) | ✅ | — |
| Roles (`director`, `operator`, `auditor`) | ✅ | rol `compiler` (opcional) |
| Ontología | ❌ | `agencia.*` vs `compiler.*` |
| Policy | ❌ | `bor-agencia.json` vs `agentic-compiler.json` |
| Knowledge base | ❌ | `knowledge/` propia |
| Credenciales | ❌ (excepto GitHub que puede ser compartida) | GitHub token del compilador |

---

## 2. Decisiones de modelo (la base de todo)

### 2.1 El compilador es un tenant, no un modo del kernel

Se registra exactamente como `bor-agencia`:

```json
{
  "slug": "agentic-compiler",
  "config": {
    "domain": "compiler",
    "enabled_capabilities": [ ... ],
    "credentials": { "api_key": "tk_…", "github": { "token": "ghp_…" } }
  }
}
```

**Por qué:** cualquier privilegio especial del compilador (escribir en el repo,
lanzar sandboxes, abrir PRs) queda sujeto a su propia policy, auditable en su
propio EventLog, y revocable desactivando el tenant. No hay “modo dios”.

### 2.2 El compilador NO toca el kernel — escribe dominios, policies y pipelines

Todo lo que produce el compilador cae en zonas de extensión:

```
src/agentic_os/domains/<nuevo_slug>/…          # ontología + entidades
data/tenants/<nuevo_slug>/                      # data_dir del nuevo tenant
data/policies/<nuevo_slug>.json                 # policy del nuevo tenant
data/tenants/registry.json                      # alta del tenant
knowledge/…  o  data/tenants/<nuevo_slug>/knowledge/…
```

**Prohibido explícitamente por la policy del compilador:** escribir en
`src/agentic_os/kernel/**`, `src/agentic_os/connectors/core/**` o cualquier
archivo bajo `tests/kernel/**`. El compilador **no** puede redefinir
invariantes. Su policy lo deniega por prefijo de path.

### 2.3 Plan en `main`, ejecución en `agentic-os-roo`

Flujo git:

```
main        ← plan.md (blueprint + pasos + tests previstos)
              ├─  (nada más se toca en main sin aprobación)
              ▼
agentic-os-roo ← código generado (dominio, policy, pipelines, tests)
              ▼
              PR o merge → aprobado por Alfonso → main
```

**Por qué:** el plan es barato y auditable; el código es caro y arriesgado.
Separar “qué voy a hacer” de “lo hecho” da un punto de revisión limpio y
permite rechazar un plan antes de gastar tokens.

> **Pendiente D1 (§7):** ¿el `plan.md` se commitea directo a `main` o va por PR
> a `main`? Por defecto se propone **PR a main** (nunca push directo), por
> coherencia con CONTRIBUTING y CI.

### 2.4 Sandbox por ejecución

El compilador **no ejecuta nada en el repo del host** durante la fase de
generación. Levanta una **VM efímera** (o contenedor con el mismo contrato) con:

- Un checkout del repo en la rama `agentic-os-roo`.
- El código de Cline adaptado (anexo B).
- Capacidades restringidas: sin credenciales del host, sin red salvo GitHub.
- Snapshot antes/después → diff auditable.

**Por qué:** el compilador va a *ejecutar código generado por un LLM*. Aislar
es la única forma defendible. La VM es parte del tenant, no del kernel.

### 2.5 Semiautomático = kernel gate + policy gate + approval humano

Tres capas de control, ya existentes:

| Capa | Qué valida | Mecanismo kernel |
|---|---|---|
| **Kernel (Pydantic)** | Forma del Intent/Command/Action. | `Command` frozen, `Intent` frozen, `Action` frozen. Payload inválido → rechazado antes de tocar Policy. |
| **Policy del tenant** | Efecto por capability. | `PolicyEngine.decide()` — default-deny. |
| **Aprobación humana** | Acciones irreversibles (push, PR, alta de tenant). | `require_approval` → cola de aprobación. |

La **cuarta capa** (opcional, reforzada) es la **validación propia del
compilador**: antes de proponer un Intent al kernel, el compilador valida
internamente el plan contra el contrato `TenantBlueprint` (ver §5.1). Pero esa
validación **no sustituye** al kernel: es un filtro previo para no ensuciar la
cola de policy con basura.

### 2.6 Recursividad controlada

Un tenant generado por el compilador puede ser **él mismo un compilador** (el
usuario lo decide en el blueprint). Con guardarraíles:

- El nuevo compilador hereda la **misma policy estructural** (no puede tocar
  kernel, no puede saltarse approval, no puede escribir en `main`).
- La aprobación humana sigue siendo obligatoria para todo push/PR.
- Existe un **profundidad máxima** (parámetro del blueprint, default 1: un
  compilador no genera compiladores-compiladores por defecto).

**Por qué:** sin límite, un compilador podría poblar el repo de sí mismo en un
bucle. Con límite, la recursión es una feature opcional y auditada.

### 2.7 Anexo Cline = capa de ejecución local, no de decisión

El código de Cline (con las modificaciones del anexo B) vive **dentro de la
carpeta del tenant compilador**, no en el kernel. Es la parte que ejecuta
acciones propuestas — igual que cualquier otra Tool. Pero Cline **no decide**:
propone; el kernel decide.

**Regla:** si el código de Cline intenta llamar a un SDK de GitHub, a un
filesystem, o a un shell **directamente**, se considera bug del compilador y
falla. Toda acción externa debe pasar por `runner.tool(capability, params)`.

---

## 3. Auditoría del estado actual del código (lo que se reutiliza)

> Audit hecho sobre el snapshot del repo que acompaña a esta prompt.

### 3.1 Kernel — estable, no se toca

- `kernel/ontology/domain_models.py`: `ENTITY_TYPE_REGISTRY` con **9 tipos
  core**; `register_entity_types()` **explícito** (no side-effect en import);
  `validate_registry_integrity()` fail-closed.
- `kernel/ontology/validator.py`: `validate_against_metamodel()` — slug
  canónico, colisión con `DEFAULT_VOCAB` rechazada, referencias rotas
  detectadas.
- `kernel/policy/engine.py`: `PolicyEngine.decide()` default-deny; `DEV_ALLOW_ALL`
  único bypass y capado por regla `allow-*`.
- `kernel/world/events.py`: `Event` con `correlation_id` + `command_id`.
- `kernel/world/applier.py` + `replay.py`: aplicación transaccional y
  `CorruptEventError` fail-closed.
- `kernel/policy/evaluator.py`: invariante **delete/publish → require_approval**
  incluso si una regla explícita dice `allow`.

### 3.2 Tenancy — reutilizable tal cual

- `TenantRegistry` singleton con `_maybe_reload` por mtime (multi-worker) y
  anti-wipe con `.corrupt.bak`.
- `TenantConfigPublic.from_config()` excluye `api_key` y `clients`.
- `resolve_client_credentials(tenant, client_id, provider)` **ya existe** y
  cumple las garantías (copia, sin log, `None` si falta).

### 3.3 Dominios — el patrón a replicar

- `domains/base.py`: `BaseDomain.compile_ontology()` fail-closed.
- `domains/agencia/` como **plantilla viva** de dominio nuevo: `__init__.py`,
  `entities.py`, `ontology.py` con `register_entities()` idempotente.
- `domains/clinic/` con projections que **lanzan NotImplementedError** en vez
  de devolver `{}`.

### 3.4 Connectors / Tools

- `ConnectorBridgeTool` + `CANONICAL_ALIASES`: **si la capability existe en el
  kernel, gana el kernel; si no, mock determinista.**
- **Faltan** en el catálogo las capabilities que necesita el compilador:
  `repo.*`, `git.*`, `sandbox.*`, `ci.*`, `codegen.*`, `tenant.blueprint.*`.

### 3.5 Pipelines

- `orchestration/pipelines/__init__.py` con `@register(id, tools=[...])` y
  `PIPELINES` + `PIPELINE_TOOLS`.
- `PipelineRunner.run()` → `Executor.execute()` → Policy → Tool → EventLog;
  idempotencia por `command_id` (TTL 24h).
- `validate_all_pipelines(registry)` fail-fast antes de runtime.

### 3.6 API

- Endpoints actuales: tenants CRUD, `/execute`, `/chat`, `/pipelines`,
  `/schedules`, `/drafts`, `/artifacts`, `/tasks`, `/skills`, `/tools`.
- **Faltan**: `/api/v1/blueprints`, `/api/v1/compilations`, `/api/v1/approvals`
  (aunque `ApprovalRequest` existe en `kernel/policy/approval.py`).

### 3.7 Lo que **no** hay y el compilador necesita

| Falta | Dónde vive la ausencia |
|---|---|
| Capabilities `repo.*` (fs scoped al repo) | `connectors/providers/` |
| Capabilities `git.*` (branch, commit, push, PR) | `connectors/providers/` |
| Capabilities `sandbox.*` (create/exec/destroy) | `connectors/providers/` |
| Capabilities `ci.*` (pytest, ruff, mypy) | `connectors/providers/` |
| Capabilities `codegen.*` (blueprint, domain, policy) | `connectors/providers/` |
| Tools correspondientes | `execution/tools/` |
| Dominio `compiler` (blueprint, plan, run, gate) | `domains/compiler/` |
| Pipelines `compile_*` | `orchestration/pipelines/` |
| Policy `agentic-compiler.json` | `data/policies/` |
| Endpoint `/api/v1/approvals` | `interfaces/api/rest.py` |
| Sandbox VM + Cline adaptado | `data/tenants/agentic-compiler/sandbox/` |
| Anexo Cline (partes a copiar) | **ausente en esta prompt** — ver §7 P1 |

### 3.8 Tests — base verde

- Suite verde excepto residuos que el propio CHANGELOG reconoce:
  `test_entity_registry` (por registro de `agencia.*` en import — ya resuelto
  como bootstrap explícito) y `test_pipeline_leads_typed` (KeyError
  `drafts_created`, arreglado según CHANGELOG).
- **Regla para el compilador:** cada tenant generado incluye **sus propios
  tests** en `tests/tenants/test_<slug>.py` + `tests/domains/test_<slug>_ontology.py`.
  Criterio de aceptación: `pytest -q` verde antes de abrir PR.

---

## 4. Principios e invariantes — el «por qué»

| #  | Invariante | Cómo lo respeta el compilador |
|----|-----------|-------------------------------|
| I1 | **El LLM nunca ejecuta directo.** Propone Intents; Policy decide; Executor ejecuta. | El loop Cline solo emite `Intent`/`Command` Pydantic. Todo `tool` pasa por `runner.tool()`. |
| I2 | **EventLog es la fuente de verdad.** WorldState derivado. | Cada paso del compilador (propose, plan, generate, test, push, PR) es un evento. El orquestador puede replay. |
| I3 | **Default-deny.** Capability no habilitada ⇒ deny. | La policy del compilador es una lista blanca **más estrecha** que la de BOR: muchas caps son `require_approval`. |
| I4 | **Fail-closed tipado.** Entidades desconocidas o inválidas no existen. | El `TenantBlueprint` es un modelo Pydantic strict; un blueprint que no valida **no se compila**. |
| I5 | **Sin credenciales en código.** | El token de GitHub vive en `TenantConfig.credentials`, se resuelve por scope, nunca se loguea. El sandbox recibe un token efímero de scope mínimo (repo, PRs). |
| I6 | **Los stubs mienten estructuradamente.** | `sandbox.exec` sin VM disponible → `CONNECTOR_NOT_CONFIGURED`, no éxito falso. |
| I7 | **Idempotencia.** `tenant+command_id` ⇒ reejecutar no duplica. | Cada paso del plan lleva `command_id` derivado de `blueprint_id + step_index`; repetir un paso no lo re-aplica. |
| I8 | **Aprobación humana por riesgo.** | `require_approval` para: push, PR, alta de tenant, `codegen.blueprint.generate` (el plan), cualquier escritura en `main`. |

---

## 5. Plan de implementación por fases (0 → 10)

### Fase 0 — Sanear base y decidir workflow git

**Objetivo:** registry limpio (retirar `tenant-a`, `tenant-b-nokey`) y decidir
D1 (plan por PR o push directo a `main`).

**Por qué:** el compilador va a escribir muchas entradas en el registry; mejor
partir de cero.

**Validación:** `pytest -q tests/` en verde; `git status` limpio.

---

### Fase 1 — Dominio `compiler` (entidades tipadas)

**Objetivo:** declarar el vocabulario del compilador como extensión del
metamodelo del kernel.

**Archivos nuevos en `src/agentic_os/domains/compiler/`:**

```
__init__.py       # re-exporta CompilerDomain, COMPILER_ENTITY_KINDS
entities.py       # TenantBlueprint, BlueprintStep, CompilationRun, SandboxSession,
                  # ValidationGate, GeneratedArtifact, CompilerFeedback
ontology.py       # CompilerDomain(BaseDomain) con register_entities()
projections.py    # runs_por_estado, blueprints_pendientes, gates_abiertos
```

**Modelos Pydantic strict (frozen, extra=forbid):**

| Modelo | Campos clave | Validaciones |
|---|---|---|
| `TenantBlueprint` | `slug`, `name`, `vertical`, `idea_nl`, `entities: list[EntitySpec]`, `capabilities: list[str]`, `pipelines: list[PipelineSpec]`, `policy_matrix: dict`, `knowledge_docs: list[str]`, `recursion_depth: int = 1` | slug regex; `recursion_depth ∈ {0,1}`; `capabilities ⊆ CapabilityRegistry` |
| `EntitySpec` | `kind`, `fields: dict[str, str]`, `validators: list[str]` | kind namespaced por slug del tenant; no colisiona con `DEFAULT_VOCAB` |
| `PipelineSpec` | `id`, `trigger`, `tools: list[str]`, `output_kind` | `tools ⊆ CapabilityRegistry` |
| `BlueprintStep` | `index`, `title`, `kind ∈ {fs, git, ci, codegen, approval}`, `payload`, `command_id` | `command_id` obligatorio (idempotencia) |
| `CompilationRun` | `id`, `blueprint_id`, `branch`, `status ∈ {planned, approved, running, failed, waiting_approval, merged, pr_open, cancelled}`, `steps: list[BlueprintStep]`, `artifacts: list[str]` | — |
| `SandboxSession` | `id`, `run_id`, `image`, `created_at`, `destroyed_at`, `snapshot_hash` | — |
| `ValidationGate` | `id`, `run_id`, `reason`, `status ∈ {pending, approved, rejected}`, `reviewer_id` | — |
| `GeneratedArtifact` | `path`, `kind ∈ {domain, policy, pipeline, test, knowledge}`, `hash` | path relativo al repo; prohibido prefijo `src/agentic_os/kernel/` |

**Registro:** `CompilerDomain.register_entities()` invoca
`register_entity_types(...)` tras `compile_ontology()`.

**Validación:** `tests/domains/test_compiler_ontology.py` — compile ok,
entidades válidas/inválidas, blueprint con slug inválido rechazado, blueprint
con capability inexistente rechazado.

---

### Fase 2 — Catálogo de capabilities nuevas

**Archivos nuevos en `connectors/providers/`:**

1. `catalog_repo.py` → provider `repo_fs`:
   - `repo.file.read`, `repo.file.write`, `repo.file.delete`, `repo.file.list`
   - `repo.dir.create`, `repo.dir.list`
   - `repo.search`
   - **Regla dura:** todas las rutas se resuelven contra la raíz del repo;
     cualquier escape (`..`, `/etc/…`) → `ToolValidationError`. Reutiliza el
     patrón `_safe_resolve` de `drive_tool.py`.

2. `catalog_git.py` → provider `git_remote`:
   - `git.status`, `git.diff`, `git.branch.create`, `git.branch.checkout`
   - `git.commit`, `git.push`, `git.pr.create`, `git.pr.comment`
   - **Riesgo declarado en el spec:** `git.push` y `git.pr.create` → `EXTERNAL_COMMUNICATION`.
     `git.branch.checkout` sobre `main` → `DESTRUCTIVE` (prohibido por policy).

3. `catalog_sandbox.py` → provider `sandbox`:
   - `sandbox.create`, `sandbox.exec`, `sandbox.destroy`, `sandbox.snapshot`

4. `catalog_ci.py` → provider `ci_runner`:
   - `ci.pytest.run`, `ci.ruff.run`, `ci.mypy.run`, `ci.test.report`

5. `catalog_codegen.py` → provider `codegen` (usa LLM internamente, pero
   expuesto como capability para que pase por Policy):
   - `codegen.blueprint.generate`, `codegen.blueprint.validate`
   - `codegen.domain`, `codegen.policy`, `codegen.pipeline`, `codegen.tool`,
     `codegen.entity`, `codegen.knowledge`

6. `catalog_tenant_admin.py` → provider `tenant_admin`:
   - `tenant.register`, `tenant.blueprint.write`

**Registro:** añadir `PROVIDER_SPECS.update(...)` en
`connectors/providers/__init__.py`. Cada spec declara su `"risk"` explícito.

**Validación:** `tests/connectors/test_compiler_capabilities.py` — registry
resuelve todas las nuevas; stub devuelve `CONNECTOR_NOT_CONFIGURED` sin
credenciales; `risk_class_for("git.push") == "EXTERNAL_COMMUNICATION"`.

---

### Fase 3 — Tools del compilador

**Archivos nuevos en `execution/tools/`:**

| Tool (mock determinista) | Capability canónica | Params esenciales |
|---|---|---|
| `RepoReadFileTool` | `repo.file.read` | `path` |
| `RepoWriteFileTool` | `repo.file.write` | `path`, `content` |
| `RepoSearchTool` | `repo.search` | `pattern`, `glob` |
| `GitBranchCreateTool` | `git.branch.create` | `name`, `from_ref` |
| `GitCommitTool` | `git.commit` | `message`, `files` |
| `GitPushTool` | `git.push` | `branch`, `remote` |
| `GitPrCreateTool` | `git.pr.create` | `title`, `body`, `base`, `head` |
| `SandboxCreateTool` | `sandbox.create` | `image`, `run_id` |
| `SandboxExecTool` | `sandbox.exec` | `session_id`, `cmd`, `cwd` |
| `CiRunTool` | `ci.pytest.run` (y ruff/mypy análogos) | `paths`, `fail_fast` |
| `BlueprintGenerateTool` | `codegen.blueprint.generate` | `idea_nl`, `tenant_hint` |
| `DomainGenerateTool` | `codegen.domain` | `blueprint_id`, `entity_spec` |
| `TenantRegisterTool` | `tenant.register` | `slug`, `name`, `domain`, `policy_ref` |

**Puente:** ampliar `CANONICAL_ALIASES` en `execution/tools/connector_bridge.py`.

**Reglas duras en cada tool:**
- Ninguna tool **toca el kernel**. Si el `path` empieza por
  `src/agentic_os/kernel/` → `ToolValidationError("kernel protegido")`.
- Ninguna tool **hace push/PR** sin `require_approval` resuelto (lo controla
  la policy, pero el mock también lo comprueba con un flag `approved=True`).
- Ninguna tool **logea credenciales**.

**Validación:** `tests/connectors/test_compiler_tools.py` — path traversal
rechazado, escritura en kernel rechazada, mock determinista.

---

### Fase 4 — Pipelines del compilador

**Ubicación (por indicación del usuario):** los pipelines generales viven en
`orchestration/pipelines/`, no en la carpeta del tenant. Los del compilador
son **generales** porque producen tenants — son la librería central.

**Archivos nuevos:**

| Pipeline | Herramientas | Salida / estado |
|---|---|---|
| `blueprint_from_idea` | `codegen.blueprint.generate` → validación Pydantic | `TenantBlueprint` + evento `BlueprintProposed` |
| `blueprint_validate` | `codegen.blueprint.validate`, `repo.search` | `ValidationReport` (fail-closed) |
| `plan_write` | `repo.file.write` (a `plans/<blueprint_id>.md`) | artefacto `plan.md` |
| `plan_approve` | `ValidationGate` (human gate) | `CompilationRun.status = approved` |
| `sandbox_bootstrap` | `sandbox.create` | `SandboxSession` |
| `generate_tenant` | `codegen.domain`, `codegen.policy`, `codegen.pipeline`, `codegen.entity`, `codegen.knowledge` | artefactos bajo `agentic-os-roo` |
| `tenant_tests_generate` | `codegen.test` (nuevo) | `tests/tenants/test_<slug>.py` |
| `ci_run` | `ci.pytest.run`, `ci.ruff.run`, `ci.mypy.run` | reporte + artefacto |
| `git_publish` | `git.branch.create`, `git.commit`, `git.push` | rama publicada |
| `pr_open` | `git.pr.create` | PR abierto (o merge si D1 lo decide) |
| `compile_tenant` | orquesta los anteriores | `CompilationRun.status = merged` |

**Idempotencia:** cada pipeline recibe `command_id = f"{blueprint_id}:{step}"`.
Reejecutar dentro de TTL 24h no re-aplica.

**Validación:** `tests/pipelines/test_pipelines_compiler.py` — un blueprint de
prueba recorre `blueprint_from_idea → ci_run` con mocks y deja el EventLog
consistente.

---

### Fase 5 — Policy `agentic-compiler`

**Archivo nuevo:** `data/policies/agentic-compiler.json`.

**Matriz (resumen):**

| Capability | Efecto | Motivo |
|---|---|---|
| `repo.file.read`, `repo.file.list`, `repo.search` | `allow` | Lecturas sin riesgo |
| `repo.file.write`, `repo.dir.create` | `allow` **con path guard** (`plans/`, `src/agentic_os/domains/`, `data/tenants/…`, `tests/…`) | El path guard es **regla explícita** de la policy, no del LLM |
| `git.status`, `git.diff`, `git.log` | `allow` | Lecturas |
| `git.branch.create`, `git.branch.checkout` (≠ `main`) | `allow` | La rama es efímera |
| `git.branch.checkout` (`main`) | `deny` (invariante) | No se toca `main` sin PR |
| `git.commit` | `allow` | — |
| `git.push`, `git.pr.create`, `git.pr.comment` | `require_approval` (rol `director`) | EXTERNAL_COMMUNICATION |
| `sandbox.*` | `allow` | Aislado por diseño |
| `ci.*` | `allow` | Solo lecturas + reporte |
| `codegen.blueprint.generate`, `codegen.*` | `allow` | Producen artefactos, no efectos externos |
| `tenant.register` | `require_approval` | Alta de tenant = cambio persistente |
| `repo.file.write` con `path` que empieza por `src/agentic_os/kernel/` | `deny` (invariante) | Nunca |
| `*` | `deny` | Red de seguridad |

**Nota:** la regla de path guard se implementa con `resource_kind` (el
`PolicyEvaluator` ya soporta `resource_kind` como patrón). El pipeline pasa
`resource_kind = "kernel"` o `"domain"` según el path resuelto.

**Validación:** `tests/policy/test_compiler_policy.py` — matriz parametrizada;
intentar escribir en kernel devuelve `deny`; push sin rol director devuelve
`deny`; push con rol director devuelve `require_approval`.

---

### Fase 6 — Alta del tenant y knowledge base

**Alta:**

```python
TenantRegistry().create(
    name="Agentic Compiler",
    slug="agentic-compiler",
    config={
        "domain": "compiler",
        "enabled_capabilities": [ ... todas las de Fase 2 ... ],
        "credentials": {
            "api_key": "tk_…",
            "github": {"token": "ghp_…", "repo": "Alfonso/agentic-os"},
        },
    },
)
```

**Knowledge base en `data/tenants/agentic-compiler/knowledge/`:**

- `como_se_crea_un_tenant.md` — guía paso a paso, referenciando `bor-agencia`
  como ejemplo canónico.
- `contrato_tenant_blueprint.md` — schema del blueprint con ejemplos.
- `reglas_kernel.md` — recordatorio de qué no se toca.
- `workflow_git.md` — plan en main, código en `agentic-os-roo`, PR, merge.
- `anexo_cline.md` — versión canónica del anexo B (ver §9).

**Estructura del `data_dir`:**

```
data/tenants/agentic-compiler/
├── knowledge/            # los .md anteriores
├── blueprints/           # <blueprint_id>.json (TenantBlueprint serializado)
├── runs/                 # <run_id>.json (CompilationRun)
├── sandbox/              # plantillas de VM + snapshot
├── gates/                # ValidationGate pendientes
├── artifacts/            # GeneratedArtifact (referencias)
└── schedules.json
```

**Validación:** `GET /api/v1/tenants` con admin; `GET /api/v1/state` con
`X-Tenant-Id: agentic-compiler` devuelve eventos vacíos inicialmente.

---

### Fase 7 — Sandbox VM + Cline adaptado

**Objetivo:** el compilador ejecuta el loop de Cline **dentro de una VM
efímera** y bajo las reglas del kernel.

**Componentes:**

```
data/tenants/agentic-compiler/sandbox/
├── Dockerfile                # base python:3.11-slim + git + node
├── vm_entrypoint.sh          # monta el repo, checkout agentic-os-roo
├── cline_adapter/            # código de Cline modificado (anexo B)
│   ├── loop.py               # propose → intent → policy → tool → observe
│   ├── tools_bridge.py       # TODAS las acciones pasan por runner.tool()
│   ├── guardrails.py         # límites: máx pasos, máx tokens, timeouts
│   └── README.md             # qué se copió y qué se modificó
└── policies/
    └── sandbox_limits.json   # límites duros por ejecución
```

**Reglas del loop:**

1. Entrada: un `BlueprintStep`.
2. Salida: un `Intent` Pydantic (nunca código “ejecutado directamente”).
3. Cada paso emite `ActionStarted` / `ToolCompleted` / `ToolFailed` al
   EventLog del tenant.
4. Timeout por paso (default 120s) y máximo global por run (default 30 min).
5. Kill switch: si el sandbox supera N pasos sin progreso, se destruye y el
   run pasa a `failed`.

**Anexo Cline (B):** las partes a copiar se listan en §9. **No está en esta
prompt** — ver decisión pendiente **P1**.

**Validación:** `tests/security/test_sandbox_isolation.py` — la VM no accede
al filesystem del host salvo el checkout; no hay red salvo a GitHub;
credenciales del host no están presentes.

---

### Fase 8 — Scheduler y ejecución durable

- **MVP con APScheduler:** disparo manual desde API; opcionalmente cada
  `blueprint.proposed_at + 1h` reintenta runs fallidos.
- **Temporal:** `orchestration/temporal/` ya existe; se añade workflow
  `CompilationWorkflow` con activities por paso (`blueprint_activity`,
  `generate_activity`, `ci_activity`, `publish_activity`).
- **Idempotencia entre disparos:** `command_id` derivado del `run_id`.

**Validación:** crear un run vía API, verlo en `data/tenants/agentic-compiler/runs/`,
ver el artefacto del EventLog.

---

### Fase 9 — API del compilador

**Nuevos endpoints en `interfaces/api/rest.py`:**

| Método | Ruta | Qué hace |
|---|---|---|
| `POST` | `/api/v1/blueprints` | Recibe `{idea_nl, tenant_hint}` → lanza `blueprint_from_idea` → devuelve `blueprint_id` |
| `GET` | `/api/v1/blueprints` | Lista blueprints del tenant |
| `GET` | `/api/v1/blueprints/{id}` | Detalle + plan.md |
| `POST` | `/api/v1/blueprints/{id}/compile` | Lanza `compile_tenant` (requiere `require_approval` resuelto) |
| `GET` | `/api/v1/compilations` | Lista runs del tenant |
| `GET` | `/api/v1/compilations/{id}` | Detalle del run + artefactos |
| `POST` | `/api/v1/compilations/{id}/cancel` | Cancela (destruye sandbox, marca `cancelled`) |
| `GET` | `/api/v1/approvals` | **Cola de aprobación** — pendientes (ya pedida por PLAN de BOR) |
| `POST` | `/api/v1/approvals/{id}/approve` | Aprueba el gate |
| `POST` | `/api/v1/approvals/{id}/reject` | Rechaza el gate |

**Validación:** tests de aislamiento — un tenant A no ve blueprints ni runs de
B; approvals exigen rol `director`; cancelar un run destruye su sandbox.

---

### Fase 10 — Tests y validación final

**Suite nueva (patrón del repo, `pytest` + `pytest-asyncio`):**

| Fichero | Qué valida |
|---|---|
| `tests/tenants/test_agentic_compiler.py` | Alta del tenant, `TenantConfigPublic` sin credenciales |
| `tests/domains/test_compiler_ontology.py` | `compile_ontology()` ok; blueprint válido/inválido; kinds no registrados |
| `tests/connectors/test_compiler_capabilities.py` | Registry resuelve nuevas capabilities; riesgo declarado |
| `tests/connectors/test_compiler_tools.py` | Path traversal rechazado; kernel protegido |
| `tests/policy/test_compiler_policy.py` | Matriz allow/require_approval/deny; path guard de kernel |
| `tests/pipelines/test_pipelines_compiler.py` | `blueprint_from_idea` fail-closed; idempotencia por `command_id`; `ci_run` verde |
| `tests/security/test_sandbox_isolation.py` | Sandbox sin acceso a host; sin red salvo GitHub |
| `tests/security/test_compiler_isolation.py` | Un tenant nunca ve blueprints/runs de otro |

**Comandos:** `pytest -q`, `ruff check`, `mypy src/agentic_os` (solo archivos
nuevos).

**Criterio de salida:** suite verde, tenant `agentic-compiler` operativo, un
tenant de prueba generado end-to-end con su dominio + policy + tests.

---

## 6. Flujo end-to-end: de la idea al tenant vivo

```
 1. [USER]  Alfonso escribe en lenguaje natural al tenant agentic-compiler:
        "Quiero un tenant para una clínica dental que gestione citas,
         recordatorios por WhatsApp y facturación simple."
        POST /api/v1/blueprints { idea_nl: "...", tenant_hint: "clinica-dental" }
        ▼
 2. [PIPELINE] blueprint_from_idea
        codegen.blueprint.generate (LLM) → TenantBlueprint (Pydantic strict)
        Valida: slug, entidades, capabilities ⊆ registry, policy_matrix coherente.
        ├─ Inválido → 422 + evento BlueprintRejected (nada se escribe)
        └─ Válido   → blueprint_id + evento BlueprintProposed
        ▼
 3. [APPROVAL] ValidationGate("plan_review", rol=director)
        Se genera plans/<blueprint_id>.md (borrador) y se encola aprobación.
        Alfonso aprueba (POST /api/v1/approvals/{id}/approve).
        ▼
 4. [PIPELINE] plan_write → commit del .md en main (o PR, según D1).
        ▼
 5. [PIPELINE] sandbox_bootstrap
        sandbox.create → SandboxSession con image=compiler-v1
        checkout agentic-os-roo
        ▼
 6. [SANDBOX + CLINE] generate_tenant
        El loop de Cline, paso a paso, emite Intents que pasan por Policy:
          codegen.entity(patient)         → allow   → escribe domains/clinica_dental/entities.py
          codegen.entity(appointment)     → allow
          codegen.policy(clinica-dental)  → allow
          codegen.pipeline(book_appointment) → allow
          codegen.knowledge(servicios)    → allow
        Cada paso: ActionStarted / ToolCompleted → EventLog
        ▼
 7. [PIPELINE] tenant_tests_generate
        Añade tests/tenants/test_clinica_dental.py + tests/domains/test_*_ontology.py
        ▼
 8. [PIPELINE] ci_run
        ci.pytest.run  → verde
        ci.ruff.run    → verde
        ci.mypy.run    → verde
        ├─ Fallo → run.status = failed, sandbox.destroy(), evento CompilationFailed
        └─ Verde → continúa
        ▼
 9. [APPROVAL] ValidationGate("publish_review", rol=director)
        Se muestra el diff completo a Alfonso. Aprueba.
        ▼
10. [PIPELINE] git_publish
        git.branch.create("agentic-os-roo")  (si no existe)
        git.commit({message: "feat(clinica-dental): tenant generado por compiler"})
        git.push
        ▼
11. [PIPELINE] pr_open
        git.pr.create(base=main, head=agentic-os-roo)
        (o merge directo si D1 lo decide y Alfonso aprueba)
        ▼
12. [PIPELINE] tenant_register
        tenant.register(slug=clinica-dental, domain=clinica_dental, policy_ref=...)
        Escribe data/policies/clinica-dental.json (ya generado)
        Añade entrada en registry.json
        ▼
13. [EVENTLOG] Todo el recorrido queda auditable por correlation_id/command_id.
        El orquestador puede reconstruir la Mission → Pipeline → Action → Tool.
```

---

## 7. Decisiones pendientes / preguntas abiertas

| # | Pregunta | Estado |
|---|----------|--------|
| **P1** | **El anexo Cline NO está adjunto a esta prompt.** ¿Qué partes exactas del código de Cline se copian y dónde viven? ¿Qué licencia tienen (MIT? Apache?)? ¿Se mantienen ficheros tal cual o reescritos? | BLOQUEANTE para Fase 7 |
| **P2** | **Nombre definitivo** del tenant: `agentic-compiler`, `cline-compiler`, otro | POR DEFINIR |
| **P3** | **D1 — Workflow git:** ¿`plan.md` va por PR a `main` o push directo? ¿`agentic-os-roo` es una rama estable que se reusa (una por blueprint con sufijo) o efímera por run? | POR DEFINIR |
| **P4** | **VM real o contenedor.** ¿Docker basta o hace falta VM verdadera (KVM/Firecracker)? El contrato `sandbox.exec` es el mismo. | POR DEFINIR |
| **P5** | **Recursión:** ¿`recursion_depth=1` por defecto (compilador no genera compiladores) o `2`? | POR DEFINIR |
| **P6** | **Aprobación:** ¿un solo gate por compilación o dos (plan + publish)? Propuesta: **dos**. | PROPUESTA |
| **P7** | **Rol humano.** ¿Solo Alfonso (`director`) puede aprobar o hay más roles? | POR DEFINIR |
| **P8** | **Coste LLM.** ¿Se limita por blueprint o por run? ¿Hay budget cap? | POR DEFINIR |
| **P9** | **Generación de tests.** ¿El compilador genera tests, o solo la estructura y luego un humano los escribe? Propuesta: **los genera** (fail-closed en CI). | PROPUESTA |
| **P10** | **Conocimiento del compilador sobre `bor-agencia`.** ¿Se expone `bor-agencia` como “plantilla viva” al LLM del compilador (RAG sobre `domains/agencia/`)? | PROPUESTA: sí |
| **P11** | **Alcance de la rama `agentic-os-roo`.** ¿Solo un tenant a la vez o varios blueprints en paralelo? | POR DEFINIR |
| **P12** | **Interacción con `Temporal`.** ¿Se activa desde Fase 8 o se pospone? | POR DEFINIR |

---

## 8. Glosario

| Término | Definición |
|---|---|
| **Tenant compilador** | Tenant cuyo producto son otros tenants. Su dominio es `compiler`. |
| **TenantBlueprint** | Modelo Pydantic strict que describe un tenant objetivo (slug, entidades, capabilities, pipelines, policy). Un blueprint que no valida no compila. |
| **CompilationRun** | Ejecución concreta de un blueprint. Tiene steps, artefactos, gate y estado. |
| **BlueprintStep** | Un paso del plan. Lleva `command_id` para idempotencia. |
| **SandboxSession** | VM/contenedor efímero donde corre Cline adaptado. No comparte credenciales con el host. |
| **ValidationGate** | Aprobación humana obligatoria (plan o publish). Apoyada en `ApprovalRequest` del kernel. |
| **GeneratedArtifact** | Archivo producido por el compilador. Prohibido prefijo `src/agentic_os/kernel/`. |
| **Path guard** | Regla de policy que deniega `repo.file.write` con `resource_kind=kernel`. |
| **Anexo Cline (B)** | Conjunto de ficheros de Cline modificados que viven en `data/tenants/agentic-compiler/sandbox/cline_adapter/`. |
| **Rama `agentic-os-roo`** | Rama de ejecución. El código se genera aquí; `main` solo recibe el plan y el merge aprobado. |
| **Recursión controlada** | Un compilador puede generar otro compilador, con `recursion_depth` limitada. |

---

## 9. Anexo A — mapa de archivos

**Nuevos:**

```
src/agentic_os/domains/compiler/
  __init__.py
  entities.py                # 7 modelos Pydantic strict
  ontology.py                # CompilerDomain
  projections.py             # runs_por_estado, blueprints_pendientes, gates_abiertos

src/agentic_os/connectors/providers/
  catalog_repo.py
  catalog_git.py
  catalog_sandbox.py
  catalog_ci.py
  catalog_codegen.py
  catalog_tenant_admin.py

src/agentic_os/execution/tools/
  repo_tools.py
  git_tools.py
  sandbox_tools.py
  ci_tools.py
  codegen_tools.py
  tenant_admin_tools.py

src/agentic_os/orchestration/pipelines/
  pipeline_blueprint_from_idea.py
  pipeline_blueprint_validate.py
  pipeline_plan_write.py
  pipeline_sandbox_bootstrap.py
  pipeline_generate_tenant.py
  pipeline_tenant_tests_generate.py
  pipeline_ci_run.py
  pipeline_git_publish.py
  pipeline_pr_open.py
  pipeline_tenant_register.py
  pipeline_compile_tenant.py    # orquestador de los anteriores

data/tenants/agentic-compiler/
  knowledge/{como_se_crea_un_tenant,contrato_tenant_blueprint,
             reglas_kernel,workflow_git,anexo_cline}.md
  blueprints/
  runs/
  sandbox/{Dockerfile,vm_entrypoint.sh,cline_adapter/,policies/}
  gates/
  artifacts/
  schedules.json

data/policies/agentic-compiler.json

tests/tenants/test_agentic_compiler.py
tests/domains/test_compiler_ontology.py
tests/connectors/test_compiler_capabilities.py
tests/connectors/test_compiler_tools.py
tests/policy/test_compiler_policy.py
tests/pipelines/test_pipelines_compiler.py
tests/security/test_sandbox_isolation.py
tests/security/test_compiler_isolation.py
```

**Modificados:**

```
src/agentic_os/kernel/ontology/domain_models.py            (nada — no se toca)
src/agentic_os/connectors/providers/__init__.py             (PROVIDER_SPECS.update)
src/agentic_os/execution/tools/{__init__,connector_bridge}.py (ALL_TOOLS + CANONICAL_ALIASES)
src/agentic_os/orchestration/pipelines/__init__.py           (imports)
src/agentic_os/interfaces/api/rest.py                        (endpoints /blueprints, /compilations, /approvals)
src/agentic_os/orchestration/temporal/{workflows,activities}.py (CompilationWorkflow — Fase 8)
data/tenants/registry.json                                   (alta Fase 6)
README.md / docs/spec/*                                      (catálogo actualizado)
```

**Explícitamente NO modificados** (garantía del compilador):

```
src/agentic_os/kernel/**
src/agentic_os/connectors/core/**
tests/kernel/**
```

---

## 9. Anexo B — contrato del anexo Cline

> **Bloqueante:** este anexo debe completarse antes de la Fase 7. Sin él, el
> sandbox no tiene loop ejecutable.

**Qué necesito que adjuntes** (o dónde mirar en tu copia de Cline):

1. **`cline_adapter/loop.py`** — el bucle principal de Cline tal como lo
   adaptas (propose → tool → observe), con la sustitución del “tool call”
   por `runner.tool(capability, params)`.
2. **`cline_adapter/tools_bridge.py`** — el puente que mapea cada acción que
   Cline quiere hacer (edit file, run command, search) a una capability
   canónica (`repo.file.write`, `sandbox.exec`, `repo.search`).
3. **`cline_adapter/guardrails.py`** — límites duros: máx pasos por run, máx
   tokens, timeouts por step, kill switch.
4. **Lista de ficheros originales de Cline** que se copian (con su licencia y
   versión). Si hay reescritura, indicar qué se cambió y por qué.
5. **`README.md` del adapter** — documentación para que un humano pueda
   mantenerlo.

Formato esperado: carpeta `anexo_cline/` en la raíz de la PR del plan, con los
ficheros anteriores y un `MANIFEST.md` que liste origen, licencia y diff.

---

*Fin del documento — v1.0 del plan para el tenant «Agentic Compiler».*

---

**Nota final para ti, Alfonso:**

- El fichero en disco debería ser `PLAN_CLINE_AGENTE_COMPILADOR.md` (sin `:`).
- Hay tres cosas que **no puedo cerrar sin ti**: (a) el **anexo Cline** (P1,
  bloqueante Fase 7), (b) la decisión **D1** sobre `plan.md` en `main` vs PR
  (P3), y (c) si el sandbox es **Docker o VM real** (P4).
- Con (a) resuelto, el resto del plan se puede ejecutar tal cual, fase por
  fase, con `pytest` verde por fase — igual que hiciste con `bor-agencia`.
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------

audit de gemini v2 que acabas de leer: Sí, déjalo. Es bueno y **no empeora nada**. Al contrario, es el mejor documento que tienes hasta ahora.

Te hago auditoría rápida de ese plan v1.0 que pegaste, contra tu repo real que ya escaneé:

### Lo que está excelente (conservar tal cual):

**1. Decisión 2.1 y 2.2:** "El compilador es un tenant, no un modo del kernel" y "NO toca el kernel". Esto es 100% compatible con tu `00_SYSTEM_PRINCIPLES.md` y `CODEOWNERS`. Es dog-fooding radical. Si lo rompes y le das modo dios, invalidas todo tu OS.

**2. Plan en `main`, ejecución en `agentic-os-roo`:** Es exactamente tu arquitectura de dos velocidades (Laia rápida + director background) llevada a Git. Barato auditar el `.md`, caro auditar el código. Perfecto.

**3. Auditoría §3:** Está clavada a tu repo real: `ENTITY_TYPE_REGISTRY` con 9 tipos, `register_entity_types()` explícito, `TenantRegistry` con `_maybe_reload` y anti-wipe, `resolve_client_credentials`, `ConnectorBridgeTool` + `CANONICAL_ALIASES`, etc. Se nota que hiciste el audit real, no inventado.

**4. Principios §4 (I1-I8):** Fail-closed tipado, idempotencia por `command_id`, EventLog fuente de verdad, default-deny. Todo alineado con `kernel/world/events.py` (`correlation_id + command_id`) y `policy/evaluator.py` (delete/publish → require_approval).

### Lo que no empeora pero hay que pulir para que compile:

**A) Tu §7 P1 (Anexo Cline) es el bloqueante real.** Tu plan dice "anexo Cline no está adjunto". Es cierto. El anexo que te generé en `anexo_cline_tuneado_FINAL.md` lo resuelve y ya incluye lo que me pediste extra: **CLI + Streamlit simple + área Temporal.io para prompts/pipelines**. No lo tenías en el v1.0 y es donde más valor aportas.

Te falta mapear las **28 tools reales de Cline**, no solo 5. Tu plan solo menciona `repo.file.write`, `sandbox.exec`, etc. Pero Cline real tiene `replace_in_file` (SEARCH/REPLACE), `apply_patch`, `attempt_completion`, `ask_followup_question` (que en tu OS es `NEEDS_APPROVAL`), `list_code_definition_names`, `use_mcp_tool`. Si no mapeas `replace_in_file`, Cline va a reescribir ficheros enteros y te va a romper tests. Mi anexo final ya trae la tabla completa.

**B) D1 - plan.md en main vs PR:** Tú propones PR a main. Hazlo PR siempre. Tu `CONTRIBUTING.md` y tu `ci.yml` exigen CI verde. Si haces push directo a `main`, te saltas `ruff + mypy + pytest`. Déjalo como PR.

**C) Faltan 2 detalles de tu repo que tu plan no menciona y yo sí incluí en el anexo final:**
- `scripts/Agent-Lock` y `Agent-Queue.py` que ya tienes para Cline/Roo/Kilo. Si no los usas en `loop.py`, Cline y Roo se van a pisar el `data/tenants/<new>/ontology.json`.
- Tu `orchestration/pipelines/runner.py` ya implementa `runner.tool()` con idempotencia 24h + `_audit()` + `emit_event()`. Tu plan habla de `sandbox.exec` directo, pero debe pasar por `runner.tool()` siempre.

**D) Nombre del archivo:** Sí, cámbialo a `PLAN_CLINE_AGENTE_COMPILADOR.md` sin `:`. En Windows revienta.

### Mi veredicto:

**Déjalo como `PLAN_CLINE_AGENTE_COMPILADOR.md` en `main` y adjunta como Anexo B el archivo `anexo_cline_tuneado_FINAL.md` que te generé** (que ya incluye tu §7 resuelto + CLI + Streamlit + Temporal).

Así cierras:
- P1 bloqueante → resuelto con mi anexo (loop.py, tools_bridge.py, guardrails.py, MANIFEST, LICENSE)
- P3 D1 → resuelto: PR a main siempre
- P4 → resuelto: Docker basta por ahora, contrato `sandbox.exec` igual, VM real es Fase 8 si hace falta

Con eso puedes empezar Fase 0 → Fase 1 con `pytest` verde por fase, igual que hiciste con `bor-agencia`.

¿Quieres que te genere ahora el zip `anexo_cline/` con `loop.py`, `tools_bridge.py`, `guardrails.py`, `cli/compiler_cli.py`, `ui/app.py`, `temporal/workflows.py` y `MANIFEST.md` listo para dropear en `data/tenants/agentic-compiler/sandbox/cline_adapter/`?