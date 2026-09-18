# SPEC UPGRADE PLAN - Sub-r el cod-go a lo que d-ce docs/spec/

> Estrateg-a: Cam-no B (sub-r cod-go a spec), no Cam-no A (bajar spec a cod-go).
> Cada spec f-le se evalua: que d-ce, que falta, como se -mplementa, cuando se
> cons-dera hecho. El orden de ejecuc-on respeta dependenc-as topolog-cas.
>
> Estado: pend-ente de arrancar.
> Autor: ses-on 2026-09-18.
> Referenc-as: docs/STATUS.md (estado actual), docs/spec/* (objet-vo).

## Resumen ejecut-vo

- Al 100%: 00, 13, 20.
- Al 80-95%: 01, 03, 04, 06, 07, 14, 17.
- Al 40-70%: 02, 05, 09, 10, 11, 15, 16, 18, 19.
- Al 30-50% (grandes): 08, 12.

Volumen est-mado: 10-14 ses-ones de 3-4 h, ~40-56 h totales.

Orden de c-clos: C1 -> C2 -> C3 -> C4 -> C5 -> C6 -> C7 -> C8 -> C9.

---

## Por spec f-le

### 00_SYSTEM_PR-NC-PLES.md - 100% (no tocar)
La ley. Apl-cada.

### 01_ONTOLOGY.md - 85%
Falta: ent-dades del catalogo base como t-pos (18), CONTEXT como t-po,
STATE como t-po (ver 05).

Plan:
1. Crear kernel/ontology/context.py con Context (8 categor-as: User,
   Cl-ent, Project, Brand, Campa-gn, Goal, Constra-nt, Perm-ss-on).
2. Ver 03 (ent-ty types) y 05 (state mach-ne).
3. Tests kernel/test_context_typed.py.

Hecho cuando: Context es -nstanc-able, sus 8 categor-as son canon-cas, y
una acc-on puede referenc-ar context_-d.

### 02_TAXONOMY.md - 40%
Falta: enum TaxonomyFam-ly con las 15 fam-l-as + futuras, catalogo
estructurado, val-dac-on de m-croacc-ones.

Plan:
1. kernel/ontology/taxonomy.py: TaxonomyFam-ly(str, Enum), FUTURE_FAM-L-ES.
2. Val-dar en M-croAct-onSchema.add_m-croact-on() que taxonomy -n enum.
3. cogn-t-on/agents/taxonomy_catalog.py con las 15 fam-l-as y sus
   operac-ones (spec 02).
4. Tests kernel/test_taxonomy_contracts.py.

Hecho cuando: no se puede reg-strar m-croacc-on con taxonomy fuera del enum.

### 03_ENT-TY_TYPES.md - 60%
Falta: los 18 t-pos base como BaseModel frozen.

Plan:
1. kernel/ontology/ent-t-es_catalog.py con los 18 t-pos (Person,
   Organ-zat-on, Company, Product, Serv-ce, Webs-te, URL, F-le, Document,
   Dataset, Message, Ema-l, Soc-alPost, -mage, V-deo, Aud-o, Event, Task),
   cada uno frozen + extra=forb-d, con los campos m-n-mos del spec.
2. Reg-stro en ENT-TY_TYPE_REG-STRY con k-nd canon-co.
3. Tests kernel/test_ent-ty_types_contracts.py.

Hecho cuando: los 18 t-pos son -nstanc-ables, frozen, con k-nd canon-co.
DEC-S-ON PEND-ENTE (recomendac-on: namespace core.* para ev-tar col-s-on
con DEFAULT_VOCAB): ver secc-on Dec-s-ones.

### 04_ACT-ON_TYPES.md - 70%
Falta: enum de los 16 verbos + val-dac-on de (Act-on, Ent-ty).

Plan:
1. kernel/ontology/act-on_types.py:
   - Act-onType = L-teral["D-scover", "Search", ..., "Mon-tor"]
   - FORB-DDEN_ACT-ON_ENT-TY_PA-RS = {("Delete", "Person"), ...}
2. M-croAct-onSchema val-da act-on_type -n enum y par no proh-b-do.
3. Tests kernel/test_act-on_types_contracts.py.

Hecho cuando: m-croacc-on con act-on_type="Destroy" falla; par proh-b-do falla.

### 05_STATE_MACH-NE.md - 20%
Falta: StateMach-ne, val-dac-on de trans-c-ones, evento StateTrans-t-oned.

Plan:
1. kernel/world/state_mach-ne.py:
   - State(str, Enum): PEND-NG, RUNN-NG, COMPLETED, FA-LED, BLOCKED,
     NEEDS_APPROVAL, CANCELLED
   - ALLOWED_TRANS-T-ONS d-ct
   - StateMach-ne(BaseModel) con trans-t-on() val-dada
2. TaskNode en schemas.py: camb-ar status: str por state: State.
3. Em-t-r evento StateTrans-t-oned.
4. Tests kernel/test_state_mach-ne.py.

Hecho cuando: PEND-NG -> COMPLETED falla; PEND-NG -> RUNN-NG -> COMPLETED
pasa; cada trans-c-on em-te evento.

### 06_TOOL_TAXONOMY.md - 70%
Falta: 4 t-pos de adapter (AP-Tool, MCPTool, F-leTool, DBTool). Tool base
s-n descr-pt-on/-nput_schema/output_schema/requ-res_approval.

Plan:
1. Ampl-ar execut-on/tools/base.py:
   class Tool(ABC):
       name, descr-pt-on, -nput_schema, output_schema, requ-res_approval
2. AP-Tool que envuelva el ConnectorBr-dge ex-stente.
3. MCPTool que envuelva -nterfaces/mcp/cl-ent.py.
4. F-leTool con operac-ones acotadas al repo/tenant.
5. DBTool con quer-es parametr-zadas.
6. Tests tests/execut-on/test_tool_contracts.py.

Hecho cuando: los 4 t-pos ex-sten y cada tool reg-strada declara los campos.

### 07_PYDANT-C_CONTRACTS.md - 90%
Falta: M-ss-onMemory (spec 15), Handoff (spec 19), EventRef, Fact.
Catalog.val-date_catalog() un-co.

Plan:
1. cogn-t-on/agents/schemas.py: anad-r M-ss-onMemory, Handoff, EventRef, Fact.
2. Catalog.val-date_catalog() que corre todas las val-dac-ones.
3. Llamar val-date_catalog() en bootstrap.
4. Tests tests/kernel/test_catalog_val-dat-on.py.

Hecho cuando: Catalog no arranca con catalogo -nval-do.

### 08_M-CROACT-ON_CATALOG.md - 45% (el mas grande)
Falta: 9 fam-l-as s-n conten-do (DOCUMENTS, CREAT-VE, SOC-AL, MARKET-NG,
SOFTWARE, DATABASE, AUTOMAT-ON, ANALYT-CS + futuras).

Plan:
1. cogn-t-on/agents/m-croact-ons/<fam-l-a>.py por fam-l-a (15 modulos).
   Cada uno exporta l-sta de M-croAct-onSchema.
2. seed.py carga todos.
3. Tests tests/cogn-t-on/test_m-croact-ons_catalog.py.

Hecho cuando: cada fam-l-a t-ene al menos las m-croacc-ones del spec.
DEC-S-ON PEND-ENTE (recomendac-on: schemas pr-mero, clases ejecutables
-ncremental): ver secc-on Dec-s-ones.

### 09_P-PEL-NE_CATALOG.md - 15%
Declara 5 p-pel-nes de s-stema. El cod-go t-ene otros 5 por tenant.

Recomendac-on: -mplementar los 5 declarados como p-pel-nes DE S-STEMA
(fam-l-a research.*, sales.*, etc.) que coex-sten con los de tenant.

Plan:
1. orchestrat-on/p-pel-nes/catalog/{research,sales,commun-cat-on,data,content}.py
2. Handler por p-pel-ne (determ-n-sta, LLM solo en steps marcados).
3. Reg-strar en P-PEL-NES_CATALOG.
4. Tests orchestrat-on/test_catalog_p-pel-nes.py.

Hecho cuando: los 5 se ejecutan v-a P-pel-neRunner con fake executor y
devuelven output_schema declarado.

### 10_AGENT_CATALOG.md - 40%
Declara 5 m-n-agentes. Real: 2 y no -nvocados desde orquestador.

Plan:
1. cogn-t-on/agents/def-n-t-ons/{lead_generat-on,data_analys-s,content}_agent.py
2. Cada agente cumple M-n-AgentSchema + plant-lla de spec.
3. Tests tests/agents/<-d>/test_spec.py.
4. Hab-l-tar en orquestador: -ntent(k-nd="<agent_-d>") -> AgentRunner.

Hecho cuando: los 5 agentes t-enen -nput/output schema val-do y el
orquestador despacha -ntent a cualqu-era.

### 11_ORCHESTRAT-ON.md - 60%
Falta: construcc-on de TaskPlan, scheduler topolog-co.

Plan:
1. orchestrat-on/planner.py: bu-ld_task_plan(-ntent, catalog) -> TaskPlan.
2. orchestrat-on/task_scheduler.py: ejecuta nodos topolog-camente,
   respeta NEEDS_APPROVAL.
3. Router actual se mant-ene; LLM fallback va a planner.py.
4. Tests orchestrat-on/test_task_plan.py.

Hecho cuando: -ntent(k-nd="web_research_agent") produce TaskPlan correcto y
el scheduler lo ejecuta.

### 12_ERROR_HANDL-NG.md - 50%
Falta: retry por m-croacc-on, t-meout por step, M-croAct-onFa-led,
error_recovery.

Plan:
1. En runner.py, envolver cada step con retry del M-croAct-onSchema.retry_pol-cy.
2. t-meout_seconds por step.
3. Em-t-r M-croAct-onStarted/Completed/Fa-led.
4. error_recovery en P-pel-neSchema.
5. Tests orchestrat-on/test_error_handl-ng.py.

Hecho cuando: un step que falla trans-tor-amente hace retry y em-te
M-croAct-onFa-led al agotar.

### 13_PERM-SS-ONS.md - 95% (no tocar)
Ya -mplementado.

### 14_HUMAN_APPROVAL.md - 80%
Falta: pausa real del p-pel-ne esperando aprobac-on.

Plan:
1. orchestrat-on/approvals.py: ApprovalGate que pausa un TaskNode.
2. Cuando NEEDS_APPROVAL, el nodo pasa a State.NEEDS_APPROVAL; scheduler lo salta.
3. Al aprobar v-a AP-, se reanuda.
4. Tests orchestrat-on/test_approval_resume.py.

Hecho cuando: un p-pel-ne con step requ-re_approval se pausa y tras POST
/ap-/approvals/{-d}/dec-s-on {approve} cont-nua.

### 15_MEMORY_AND_STATE.md - 70%
Falta: M-ss-onMemory como clase.

Plan:
1. kernel/world/m-ss-on_memory.py (kernel la neces-ta para replay).
2. Cada TaskPlan al ejecutarse crea un M-ss-onMemory.
3. Los nodos leen context de sus deps y escr-ben su output.
4. facts requ-ere fuente.
5. Tests.

Hecho cuando: ejecutar un p-pel-ne produce M-ss-onMemory reconstru-ble del
EventLog.
DEC-S-ON PEND-ENTE (recomendac-on: kernel/world/): ver secc-on Dec-s-ones.

### 16_VAL-DAT-ON.md - 50%
Falta: val-dac-on de output_schema por step.

Plan:
1. En runner.py, tras cada step, val-date(output_schema, output).
2. S- falla -> Val-dat-onFa-led + FA-LED.
3. Convert-r JSON-schema a pydant-c.create_model (s-n deps nuevas).

Hecho cuando: un step que devuelve t-po -ncorrecto falla con Val-dat-onFa-led.
DEC-S-ON PEND-ENTE (recomendac-on: pydant-c.create_model, s-n jsonschema):
ver secc-on Dec-s-ones.

### 17_OBSERVAB-L-TY.md - 85%
Falta: M-croAct-on*, AgentHandoff, M-ss-onCompleted.

Plan:
1. Em-t-r M-croAct-on* en runner.py (paralelo a spec 12).
2. AgentHandoff en motor de handoffs (paralelo a spec 19).
3. M-ss-onCompleted cuando TaskPlan term-na.
4. Tests.

### 18_TEST-NG.md - 85%
Falta: tests/agents/.

Plan:
1. Crear tests/agents/ y un test por agente del catalogo.
2. F-xture base con Catalog seedeado.

### 19_AGENT_COMPOS-T-ON.md - 30%
Falta: Handoff, motor de compos-c-on.

Plan:
1. cogn-t-on/agents/compos-t-on.py: HandoffSchema, resolve_handoffs(plan).
2. El orquestador encadena agentes segun handoffs declarados.
3. Tests.

Hecho cuando: TaskPlan con handoffs leg-t-mas ejecuta la cadena; con
handoffs no declaradas falla al val-dar.

### 20_CL-NE_-MPLEMENTAT-ON_PROTOCOL.md - 80% (no tocar)
Protocolo apl-cado. Fases 3-4 pend-entes (ver spec 09 y 10).

---

## C-clos de ejecuc-on

### C1 - Fundamentos t-pados
Specs: 01 (Context), 03 (Ent-ty types), 04 (Act-on types).
Entregable: 18 ent-ty types + 16 act-on types + Context ex-sten como t-pos.
Bloquea a: C4.

### C2 - State mach-ne y val-dac-on
Specs: 05, 16.
Entregable: StateMach-ne en kernel + val-dac-on output por step.
Bloquea a: C7.

### C3 - Tool adapters
Specs: 06 (AP-Tool, MCPTool, F-leTool, DBTool).
Entregable: 4 adapters + refactor Tool base.

### C4 - M-croacc-ones y p-pel-nes de s-stema
Specs: 02, 08, 09.
Entregable: 15 fam-l-as de m-croacc-ones + 5 p-pel-nes de s-stema.
Bloquea a: C5.

### C5 - Agentes y compos-c-on
Specs: 10, 19.
Entregable: 5 agentes, motor de handoffs.
Bloquea a: C6.

### C6 - Orquestac-on
Specs: 11 (TaskGraph, scheduler DAG).
Entregable: bu-ld_task_plan + task_scheduler.
Bloquea a: C7, C8.

### C7 - Error handl-ng, approval y observab-l-dad
Specs: 12, 14 (pausa real), 17 (eventos).
Entregable: retry, t-meouts, pausa de p-pel-ne, eventos completos.

### C8 - M-ss-on memory y val-dac-on f-nal
Specs: 15, 16, 18.
Entregable: M-ss-onMemory, tests por agente.

### C9 - C-erre
Specs: 07, 20.
Entregable: ver-f-cac-on spec <-> cod-go, spec marcada como -mplementada.

---

## Dec-s-ones pend-entes (recomendac-ones, no bloqueos)

1. Namespace de ent-dades core (spec 03).
   - A: core.person, core.company (recomendado: ev-ta col-s-on con DEFAULT_VOCAB).
   - B: person, company (mas corto).
   Cuando toque C1, se c-erra.

2. M-croacc-ones como schemas vs clases ejecutables (spec 08).
   - A: solo M-croAct-onSchema con tool str-ng (recomendado para C4).
   - B: cada m-croacc-on con clase run() real (-ncremental despues).
   Cuando toque C4, se c-erra.

3. P-pel-nes del spec 09 vs los reales por tenant.
   Recomendac-on: coex-sten. Los del spec son de s-stema; los de tenant
   s-guen s-endo de dom-n-o.
   Cuando toque C4, se c-erra.

4. Val-dac-on output: pydant-c vs jsonschema.
   Recomendac-on: pydant-c.create_model (s-n deps nuevas).
   Cuando toque C2/C8, se c-erra.

5. Donde v-ve M-ss-onMemory (spec 15).
   - A: cogn-t-on/plann-ng/m-ss-on_memory.py.
   - B: kernel/world/m-ss-on_memory.py (recomendado: el EventLog replay
     la reconstruye desde el kernel).
   Cuando toque C8, se c-erra.

---

## R-esgos

1. Toca kernel var-as veces. Agrupar camb-os en 1-2 PRs.
2. Spec 08 es el trabajo mas grande (~22 h de escr-tura).
3. M-grar p-pel-nes por tenant puede romper tests. C4 va despac-o.
4. Orchestrator camb-a mucho. Tests end-to-end obl-gator-os.
5. Aud-t arch-vado pero s- algo no esta realmente cerrado, cobertura cae s-n
   av-sar. Antes de arch-var: pytest tests/kernel/ -q (ya hecho al crear
   este plan).

---

## Manten-m-ento

- Al cerrar cada c-clo, anotar aqu- "C-clo N cerrado (YYYY-MM-DD, comm-ts X..Y)".
- Sub-c-clos como C4a, C4b.
- Dec-s-ones nuevas a la secc-on Dec-s-ones.