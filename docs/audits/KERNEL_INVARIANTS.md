# AUDIT — Kernel, Ontología, Policy y Connectores

Fecha: 2026-09-17
Rama: `master` (HEAD = `bf4491b` "chore: kernel limpio + tenants con libreria propia (pasos 6-11)")
Alcance: `src/agentic_os/{kernel,connectors,execution,contracts}` y `scripts/audit.sh` frente a
`docs/INVARIANTS.md`, `docs/GOVERNANCE.md`, `docs/PRE_PRODUCTION_CHECKLIST.md`, `docs/spec/` y `README.md`.
Tipo de documento: **diagnóstico y severidad**. No contiene propuestas de cambio de código.

---

## 0. Método y límites

- Contraste *contrato declarado* ↔ *código real*, con lectura directa de cada archivo citado.
- Los conteos (providers, mappings, capabilities, tipos de evento emitidos) se obtuvieron por
  análisis textual de los archivos, **sin importar el paquete**.
- Dos comprobaciones se **ejecutaron en runtime** fuera del repo (para no generar `__pycache__`):
  1. comportamiento del AST de Python con imports relativos;
  2. semántica de `frozen=True` de pydantic sobre un campo de tipo `set`.
  Ambas están reproducidas en §7.
- **No se ejecutó** `pytest`, `ruff`, `mypy` ni `bash scripts/audit.sh`. Todo hallazgo que dependa
  de ejecutar la suite queda marcado como *pendiente de confirmar en runtime*.
- Cada hallazgo indica los archivos y líneas concretos que lo sustentan.

## 1. Resumen de severidades

| ID | Severidad | Área | Hallazgo en una línea |
|---|---|---|---|
| AUD-01 | 🔴 BLOQUEANTE | kernel / layering | El invariante "el kernel no importa fuera del kernel" está violado, y el test que lo protege es ciego a imports relativos |
| AUD-02 | 🔴 BLOQUEANTE | kernel / policy | `PolicyEngine.decide()` no es pura: hace I/O de disco y su resultado depende del CWD del proceso |
| AUD-03 | 🔴 BLOQUEANTE | kernel / policy | `tenant_id` sin validar se interpola en la ruta del archivo de policy (lectura arbitraria de archivos) |
| AUD-04 | 🔴 BLOQUEANTE | kernel / world | Pérdida silenciosa de eventos: `kind` desconocido o `entity_deleted` se aplican como no-op con `version+1` |
| AUD-05 | 🔴 BLOQUEANTE | kernel / world | El camino tipado de eventos (`event_type` + `data`) es código muerto y, además, no mutaría el `WorldState` |
| AUD-06 | 🟠 ALTO | kernel / world | `EVENT_VOCAB` mezcla tipos de evento con un kind de dominio (`sales.lead.created`) dentro del kernel |
| AUD-07 | 🟠 ALTO | kernel / world | `EventLog` no es append-only en la práctica: lista pública mutable |
| AUD-08 | 🟠 ALTO | kernel / ontology | `DEFAULT_VOCAB` no es inmutable: `frozen` no protege los `set` internos; el test que lo parecía cubrir prueba otra cosa |
| AUD-09 | 🟠 ALTO | kernel / ontology | La ontología del tenant (`OntologyBundle`) está desconectada del estado real (`ENTITY_TYPE_REGISTRY` + `WorldState`) |
| AUD-10 | 🟠 ALTO | kernel / ontology | `ENTITY_TYPE_REGISTRY` es un global de proceso, no scoped por tenant |
| AUD-11 | 🟠 ALTO | kernel / policy | `DEV_ALLOW_ALL=true` devuelve `allow` **antes** de evaluar reglas, anulando el endurecimiento `delete`/`publish` |
| AUD-12 | 🟡 MED | kernel / policy | Matching de capabilities sin namespaces y sin precedencia de `deny` (gana la primera regla que matchea) |
| AUD-13 | 🟡 MED | kernel / policy | El endurecimiento por riesgo cubre solo los tokens `delete`/`publish`; README promete clases FINANCIAL/DESTRUCTIVE |
| AUD-14 | 🟡 MED | kernel / ontology | Dos definiciones divergentes de "kind canónico" en el mismo paquete (`vocabulary.py` vs `relations.py`) |
| AUD-15 | 🟡 MED | contratos | Tres representaciones de `Action` y dos de `ExecutionResult`; el `Executor` usa las laxas y devuelve dicts planos |
| AUD-16 | 🟡 MED | execution | `Executor.execute_action()` fuerza `tenant_id="system"` e ignora el tenant del contexto |
| AUD-17 | 🟡 MED | docs / catálogo | Los números del catálogo de conectores en README/CHANGELOG están desactualizados (44/265/187 vs 45/286/203) |
| AUD-18 | 🟡 MED | docs / tests | `tests/bugs/` no existe pero se cita como bloqueante de merge en `INVARIANTS.md` y `GOVERNANCE.md` |
| AUD-19 | 🟡 MED | tooling | `scripts/audit.sh` no puede pasar en verde: dos de sus checks apuntan a código y rutas inexistentes |
| AUD-20 | 🔵 BAJO | docs | `README.md` documenta un `frontend/` que no existe y omite dos paquetes reales |
| AUD-21 | 🔵 BAJO | higiene | Artefactos en limbo fuera de `src/`, pycache huérfanos y un hueco en `.gitignore` para runtime de tenant |
| AUD-22 | 🟡 MED | higiene / runtime | Estado de runtime **versionado**: `data/policies/*.json` está trackeado en git y cambia con cada ejecución local |

---

## 2. Hallazgos BLOQUEANTES

### AUD-01 — 🔴 El invariante "el kernel no importa fuera del kernel" está violado y su test no lo detecta

**Declarado:** `CONTRIBUTING.md` ("kernel determinista con invariantes estrictas"), `README.md`
("Kernel = invariantes"), `tests/kernel/test_no_kernel_imports_domains.py` (que enumera como
prohibidos `domains`, `orchestration`, `cognition`, `interfaces`, `connectors`, `execution`,
`infrastructure`, `agents`).

**Real — dos problemas independientes:**

1. **El test es ciego a imports relativos.** La comprobación usa solo `node.module`
   (`test_no_kernel_imports_domains.py:29-43`), ignorando `node.level`. Para
   `from ...infrastructure.tenancy import TenantRegistry`:

   | Dato del AST | Valor |
   |---|---|
   | `node.module` | `'infrastructure.tenancy'` |
   | `node.level` | `3` |
   | `node.module.startswith("agentic_os.infrastructure")` | `False` |

   → La aserción **nunca se evalúa en su forma absoluta**, y el import prohibido pasa. (Evidencia
   ejecutada: §7, prueba 1.)

2. **El kernel sí lo viola.** `src/agentic_os/kernel/policy/engine.py:73` contiene
   `from ...infrastructure.tenancy import TenantRegistry`. Es el **único** `from ...` en todo
   `kernel/` (búsqueda dirigida sobre `src/agentic_os/kernel/*.py`).

**Efecto:** el invariante de capas se cumple por convención, no por enforcement, y hoy no se cumple.
La protección queda además asimétrica: hay un test que impide `kernel → domains`, pero el mismo
test falla en impedir `kernel → infrastructure`.

---

### AUD-02 — 🔴 `PolicyEngine.decide()` no es pura (contradice "Engine pure")

**Declarado:** `kernel/policy/invariants.py:11` lista `"Engine pure"`; `docs/INVARIANTS.md:25`
afirma "`Engine pure` → `decide()` no tiene side-effects".

**Real:**

| Línea | Comportamiento observado |
|---|---|
| `kernel/policy/engine.py:83-95` | `decide()` llama a `_load_policy()`, que hace `path.exists()` + `path.read_text()` + `json.loads()` sobre un archivo en disco |
| `kernel/policy/engine.py:71-76` | `_tenant()` importa y construye `TenantRegistry()` en cada llamada, dentro de un `try/except Exception: return None` que silencia cualquier fallo de infraestructura |
| `kernel/policy/engine.py:96-98` | Si la policy está corrupta, se degrada a `default_policy(tenant_id)` **sin registrar el error** |

**Efecto:** el resultado de una decisión de autorización depende del sistema de archivos y del
estado global del registro de tenants, no solo de sus argumentos. El propio kernel declara la
pureza como invariante ejecutable en un módulo de invariantes.

**Agravante de determinismo:** la ruta es relativa al **directorio de trabajo**
(`Path(f"data/policies/{tenant_id}.json")`), y existe una configuración declarada que el kernel
ignora: `infrastructure/config/settings.py:28` (`policies_dir: str = Field(default="data/policies")`).
Un proceso arrancado desde otro directorio no cargará las policies de tenant y degradará en
silencio a `default_policy` (deny total) o a `allow` si `DEV_ALLOW_ALL` está activo.

---

### AUD-03 — 🔴 `tenant_id` sin validar se interpola en una ruta de archivo

**Real:** `kernel/policy/engine.py:83` construye `Path(f"data/policies/{tenant_id}.json")` con el
`tenant_id` recibido por parámetro, sin validación de formato. El camino `tenant_id == "system"`
(`engine.py:122-123`) llega a `_load_policy()` **directamente**, sin pasar por el registro de
tenants (que es la única validación indirecta para el resto de tenants).

No hay uso de `Path.resolve()` ni comprobación de contención, pese a que el kernel ya dispone de un
validador de slugs canónicos (`kernel/ontology/vocabulary.py:16-27`, `is_canonical_kind`).

**Efecto:** el segmento permite traversal de lectura (`data/policies/../../<x>.json`). Requiere que
el objetivo tenga extensión `.json` y que el contenido sea un JSON compatible con `Policy`, por lo
que el impacto es de lectura/existencia de archivos y de error observable, no de ejecución.

---

### AUD-04 — 🔴 Pérdida silenciosa de eventos en el `WorldState`

**Declarado:** `docs/INVARIANTS.md:15` ("**CorruptEventError** → si un evento es inválido, el replay
falla con el índice; nunca devuelve estado parcial") y `kernel/world/replay.py:8-13` ("el replay
NUNCA continua ni devuelve un estado parcial").

**Real:** `kernel/world/applier.py:14-76` ramifica exclusivamente por `event.kind` y solo reconoce
4 valores: `entity_created`, `entity_updated`, `relation_created`, `relation_deleted`. Todas las
demás ramas caen al retorno final (`applier.py:74-76`), que **incrementa `version`** sin aplicar
cambio alguno.

| Caso | Ramas existentes | Resultado real |
|---|---|---|
| `entity_deleted` | declarado en `EVENT_VOCAB` (`world/events.py:21`) | **no-op silencioso** con `version+1`; la entidad borrada permanece en el estado |
| `kind` desconocido / con errata | no validado | **no-op silencioso** con `version+1` |
| `IntentProposed`, `BackgroundProcessingDone`, `ScheduledPipeline*`, `Action*`, `Tool*`, `Pipeline*`, `ApprovalRequired`… | no tienen rama | se registran en el log y el replay los ignora |

**Segundo problema, más de fondo:** `event.kind` **no se valida contra ningún vocabulario**. La
validación contra `EVENT_VOCAB` solo se aplica al campo `event_type`
(`world/events.py:84-87`), que es justamente el campo que nadie usa (ver AUD-05). El vocabulario
existe, pero no cubre el camino que sí se ejecuta.

**Efecto:** un evento malformado o con errata produce un `WorldState` que ha perdido ese hecho sin
lanzar `CorruptEventError` ni ningún aviso: es exactamente el "estado parcial silencioso" que la
invariante declara imposible. La detección de corrupción existe y funciona (está probada en
`tests/kernel/test_worldstate_typed.py:105-125`), pero solo cubre los 4 `kind` reconocidos.

---

### AUD-05 — 🔴 El camino tipado de eventos es código muerto y no tendría efecto

**Declarado:** `kernel/world/events.py:39-88` modela dos formas de evento — tipada
(`event_type` + `data`, descrita en el comentario del módulo) y legacy (`kind` + `payload`) — y
`world/applier.py:16-18` documenta "A6/A7: entity_created y entity_updated usan event.data tipado".

**Real (medido sobre todo `src/`):**

| Medición | Resultado |
|---|---|
| Ocurrencias de `event_type=` en `src/agentic_os/**` | **0** |
| Ramas de `applier.apply()` que contemplan `event.event_type` | **0** |
| Tests del replay que usan `event_type` | **0** (`test_invariants.py:16-25` y `test_worldstate_typed.py:85-137` usan `kind=` + `payload=`) |

El módulo `world/events.py` define la vía tipada con `Generic[T]`, `data: Optional[T]` y un
validador que impide mezclar ambas formas, pero **ningún productor del sistema la usa**, y
`apply()` — el único consumidor del log junto a `replay()` — no la interpretaría si se usara:
la decisión de qué hacer con un evento depende solo de `event.kind`.

**Efecto:** hay dos contratos de evento declarados, uno de ellos sin productores ni consumidores.
Todo el tráfico real va por la vía legacy `kind` + `payload`, que es la que no está validada contra
el vocabulario (AUD-04) y la que no tiene rama para `entity_deleted`.

---

## 3. Hallazgos ALTOS

### AUD-06 — 🟠 `EVENT_VOCAB` del kernel no refleja la realidad del sistema (y filtra un dominio)

**Real:** `kernel/world/events.py:17-36` declara `EVENT_VOCAB` con 16 tipos. Contrastado con los
sitios que **construyen** `Event(kind=...)` en `src/`:

| Tipo de evento | ¿En `EVENT_VOCAB`? | Emisor verificado |
|---|---|---|
| `ActionStarted`, `ActionDenied`, `ToolCompleted`, `ToolFailed` | ✅ | `execution/executor.py:336, 241/318, 362, 290/395` |
| `ActionIdempotentHit` | ❌ | `execution/executor.py:216` |
| `ApprovalRequired` | ❌ | `execution/executor.py:264`, `interfaces/api/rest.py:657` |
| `IntentProposed` | ✅ | `orchestration/orchestrator.py:108` |
| `ScheduledPipelineFailed`, `ScheduledPipelineFinished` | ✅ | `orchestration/orchestrator.py:175`, `interfaces/api/rest.py:1082` |
| `ScheduledPipelineEnqueued` | ❌ | `interfaces/api/rest.py:1041` |
| `TemporalEnqueueFailedFallback` | ❌ | `interfaces/api/rest.py:1060` |
| `BackgroundProcessingDone`, `BackgroundProcessingFailed` | ✅ | `interfaces/api/rest.py:808, 852` |
| `CompilerChatAnswered` | ❌ | `interfaces/api/rest.py:1903` |
| `PipelineStarted`, `PipelineCompleted`, `PipelineFailed` | ❌ | `orchestration/pipelines/runner.py:126, 131, 143` (vía `_audit`, `runner.py:161-171`) |
| `entity_created`, `entity_updated`, `entity_deleted`, `relation_created`, `relation_deleted` | ✅ | no se emiten en `src/` (solo en tests) |
| `ScheduledPipelineStarted` | ✅ | ningún emisor en `src/` |
| `sales.lead.created` | ✅ | ningún emisor en `src/` |

**Dos conclusiones:**

1. **8 tipos en uso no están en el vocabulario y 7 tipos del vocabulario no se usan.** La validación
   del vocabulario no cubre el campo `kind` (AUD-04), por lo que esta divergencia no produce ningún
   error hoy: simplemente el vocabulario dejó de describir el sistema.

2. **`sales.lead.created` es un kind de dominio dentro del kernel** (`kernel/world/events.py:34`).
   Contradice el objetivo declarado del refactor vigente (`bf4491b`: "kernel limpio"; y el paquete
   `kernel/` no debe conocer dominios, según `tests/kernel/test_no_kernel_imports_domains.py`).
   Nota: es el único elemento de la lista que no es un nombre de acción de sistema, y llama la
   atención porque el enum de eventos del kernel mezcla dos convenciones a la vez
   (`PascalCase` para acciones de sistema, slug minúsculo para el kind de dominio).

*Verificación: todos los sitios de emisión citados en la tabla se comprobaron por lectura directa
del código, salvo `interfaces/api/rest.py:852` (`BackgroundProcessingFailed`), detectado por
análisis textual y no abierto línea a línea.*

### AUD-07 — 🟠 `EventLog` no es append-only en la práctica

**Declarado:** `docs/INVARIANTS.md:11` ("`Log append-only` → `EventLog.append()` no modifica, solo
añade").

**Real:** `kernel/world/events.py:99-145`. El log en memoria es un `BaseModel` **no frozen** con el
campo público `events: List[Event]` (`events.py:109`). `append()` sí valida y toma el `RLock`
(`events.py:115-123`), pero cualquier acceso directo a la lista — `log.events.append(...)` o
`log.events.clear()` — **evita** la validación de `tenant_id`, la validación de la forma del evento
y el lock de concurrencia.

La invariante se sostiene por disciplina de los llamadores, no por el tipo. No hay ningún test ni
guarda que impida escribir directamente en `log.events`.

Observación adicional (mismo archivo): `kernel/world/invariants.py:16-43` define `validate_state()` y
`check_invariants()`, que el camino de replay **no invoca** (`kernel/world/replay.py:26-41` aplica
`apply()` y valida vía los validadores pydantic de `WorldState`, `state.py:18-52`). Las dos
funciones son redundantes con los validadores del modelo y no participan en la garantía.

### AUD-08 — 🟠 `DEFAULT_VOCAB` no es inmutable (y el test que lo parecía cubrir prueba otra cosa)

**Declarado:** `docs/INVARIANTS.md:34` ("`DEFAULT_VOCAB` inmutable en runtime").

**Real:** `Vocabulary` declara sus tres campos como `Set[str]` (`kernel/ontology/vocabulary.py:9-13`).
`model_config = ConfigDict(frozen=True)` impide **reasignar** el campo, pero no impide **mutar** el
set. Evidencia ejecutada (§7, prueba 2):

| Operación | Resultado observado |
|---|---|
| `v.entities.add("evil.injected")` | **se ejecuta**; el contenido pasa a `['actor', 'evil.injected']` |
| `v.entities = {"otro"}` | bloqueado con `ValidationError` |

**Efecto:** `DEFAULT_VOCAB` (exportado desde `kernel/ontology/__init__.py:10` y usado como base por
`validate_against_metamodel`, `validator.py:166-170`) es mutable en runtime por cualquier código que
obtenga la referencia. La invariante "un dominio extiende, nunca reemplaza" no está protegida a
nivel de tipo.

**Nota de trazabilidad:** el test que por su nombre cubría esto —`tests/kernel/test_ontology_immutable_on_import.py`—
opera en realidad sobre `ENTITY_TYPE_REGISTRY` (`test_ontology_immutable_on_import.py:7, 17-37`).
`DEFAULT_VOCAB` no aparece en ese archivo. Sí existe un test que verifica que **compilar** una
ontología no altera el vocabulario (`test_ontology_bundle.py:142-145`,
`test_clinic_default_vocab_intact`), pero ese test comprueba el caso *a través de la API de
compilación*, no la inmutabilidad del objeto.

### AUD-09 — 🟠 La ontología está desconectada del estado real del sistema

**Declarado:** `docs/INVARIANTS.md:35` ("Un dominio **extiende** con namespace propio (`clinic.patient`),
nunca colisiona") y `README.md` ("Ontology separa metamodelo (invariante) de vocabulario (extensible
por dominio)").

**Real:** existen **dos caminos paralelos sin puente entre ellos.**

| Camino | Entrada | Artefacto | Consumidores reales |
|---|---|---|---|
| A — declarativo | `validate_against_metamodel(...)` (`validator.py:84-179`) | `OntologyBundle` frozen por tenant | `domains/base.py:12-45`, tests |
| B — operativo | `register_entity_types(...)` → `ENTITY_TYPE_REGISTRY` (`domain_models.py:103-133`) | clases de dominio globales | `apply()` → `WorldState` (`applier.py:42`) |

- El camino A **no registra clases de entidad**: validar una ontología no habilita nada en runtime.
- El camino B **no consulta ningún bundle**: `entity_from_payload()` resuelve contra el registro global
  y no comprueba `tenant_scope` (`domain_models.py:126-133`). Un `OntologyBundle` de otro tenant no
  restringe nada.
- `test_ontology_bundle.py:132-145` (`test_clinic_compiles_ontology`) compila la ontología de clinic
  y verifica el bundle… sin comprobar que el `WorldState` acepte o rechace nada en consecuencia.

**Agravante en el modelo de estado:** `WorldState.relations` es `Dict[str, Dict[str, Any]]`
(`state.py:15`) y `applier.py:71` lo rellena con el `payload` crudo. Por tanto el modelo tipado
`Relation` y la validación de semántica de relaciones (`ontology/invariants.py:32-79`, con
`_RELATION_SEMANTICS` para `uses`, `accesses`, `requires`…) **nunca se aplican a las relaciones que
entran en el estado del mundo**. Las invariantes declaradas "Actor -> uses -> Tool" /
"Tool -> accesses -> Resource" (`ontology/invariants.py:15-16`) gobiernan una estructura que el
pipeline de eventos no produce ni valida. Sus tests (`tests/kernel/test_ontology_contracts.py:94-131`)
construyen las relaciones a mano.

### AUD-10 — 🟠 `ENTITY_TYPE_REGISTRY` es un global de proceso, no scoped por tenant

**Real:** `kernel/ontology/domain_models.py:96` define `ENTITY_TYPE_REGISTRY: dict[str, type[BaseDomainModel]] = {}`
como estado global del proceso, y `register_entity_types()` (`domain_models.py:103-123`) **lanza
`ValueError` si el `kind` ya está registrado por otra clase** (`domain_models.py:117-122`).

**Efecto en multi-tenancy:** el primer dominio o tenant que registre un `kind` gana; el segundo que
intente registrar el mismo `kind` con otra clase provoca un error. No hay forma de tener dos tenants
con definiciones distintas del mismo `kind`, ni de aislar el registro por tenant — precisamente lo
que el resto del sistema trata como invariante (todo evento y toda entidad llevan `tenant_id`
obligatorio, `events.py:69-74` y `domain_models.py:61-66`).

Nota: el aislamiento sí existe en la *persistencia* (`data/tenants/<tenant>/…`) y en las policies
(`data/policies/<tenant>.json`), pero no en el **registro de tipos**.

### AUD-11 — 🟠 `DEV_ALLOW_ALL=true` devuelve `allow` antes de evaluar reglas

**Declarado:** `docs/PRE_PRODUCTION_CHECKLIST.md` §3 exige "dejar `DEV_ALLOW_ALL=false`", y
`PolicyEvaluator` declara como invariante del kernel que `delete`/`publish` **siempre** exigen
aprobación humana (`kernel/policy/evaluator.py:29-35, 54-60`), "una regla explícita puede añadir más
restricciones, nunca quitar esta".

**Real — el gate de desarrollo corta la evaluación antes de llegar al evaluador:**

| Línea | Comportamiento |
|---|---|
| `engine.py:158-162` | Si el tenant existe y `DEV_ALLOW_ALL` está activo → `Decision(effect="allow")` inmediato, **sin leer la policy del tenant** |
| `engine.py:131-135` | Si el tenant **no** está registrado y `DEV_ALLOW_ALL` está activo → `allow`, saltando el registry |
| `engine.py:27-40` | `default_policy()` devuelve en modo dev una regla `capability="*"`, `effect="allow"` |
| `engine.py:166-177` | La guarda que impide la regla `allow-all` en producción protege solo ese caso concreto (una regla `"*"` en el archivo), no el cortocircuito de la línea 158 |

**Efecto:** con `DEV_ALLOW_ALL=true`, un `finanza.refund.delete` o un `blog.post.publish` reciben
`allow` y **no pasan por `PolicyEvaluator`**, de modo que el endurecimiento por `delete`/`publish`
que el kernel declara "no negociable" no se aplica; las denegaciones explícitas escritas en
`data/policies/<tenant>.json` tampoco. Es una variable de entorno capaz de anular una invariante
declarada como del kernel.

---

## 4. Hallazgos MEDIOS

### AUD-12 — 🟡 Matching de capabilities sin namespaces y sin precedencia de `deny`

**Real:** dos limitaciones en `kernel/policy/evaluator.py`:

1. **Sin namespaces.** `_matches()` (`evaluator.py:14-20`) solo admite coincidencia **exacta** o el
   comodín global `*`. Un tenant no puede expresar `clinic.*` ni `crm.contact.*` en su policy,
   aunque la ontología sí trabaja con namespaces por dominio (`clinic.patient`, ver
   `test_ontology_bundle.py:30`). La única granularidad disponible es "todo" o "exacto".
2. **Sin precedencia de `deny`.** `evaluate()` (`evaluator.py:45-62`) recorre las reglas y **retorna
   en la primera coincidencia**. Con `[allow crm.contact.create, deny crm.contact.create]` el
   resultado es `allow`. El resultado depende del orden de las reglas del archivo JSON, no de que
   `deny` prevalezca. (El endurecimiento `delete`/`publish` sí tiene prioridad sobre una regla
   `allow` —`evaluator.py:54-60`—, lo que demuestra que el mecanismo de "endurecer" existe, pero
   se aplica solo a ese caso.)

Observación menor del mismo módulo: `PolicyEngine.is_allowed(tenant_id, action)` pasa `action` a la
posición de `capability` de `decide()` (`engine.py:202-214`); es correcto en efecto, pero el nombre
`action` sugiere que puede recibir otro tipo de valor. `can_for_tenant()` (`engine.py:187-200`) es una
indirección que reenvía exactamente a `decide()`.

### AUD-13 — 🟡 La clasificación de riesgo no cubre las clases que el README promete

**Declarado:** `README.md` ("Clasificación de riesgo por capability (READ_ONLY,
EXTERNAL_COMMUNICATION, FINANCIAL, DESTRUCTIVE...)").

**Real:** el único endurecimiento implementado se basa en **tokens del nombre** de la capability:
`INVARIANT_APPROVAL_SEGMENTS = {"delete", "publish"}` (`evaluator.py:35`) aplicado por
`_requires_human_approval()` (`evaluator.py:40-43`).

**Efecto:** capabilities financieras o de comunicación externa presentes en el catálogo
(`finance.refund.create`, `stripe.*`, `whatsapp.message.send`, `email.message.send`) **no disparan
aprobación humana**; solo lo hacen las que contienen literalmente `delete` o `publish`. El sistema
de clases de riesgo del README no tiene representación en el kernel de policy.

### AUD-14 — 🟡 Dos definiciones divergentes de "kind canónico" en el mismo paquete

**Real:** dos expresiones regulares distintas gobiernan el mismo concepto:

| Archivo | Patrón | Permite `.` | Consecuencia |
|---|---|---|---|
| `kernel/ontology/vocabulary.py:6` | `^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$` | ✅ | `is_canonical_kind("clinic.has_appointment") == True` |
| `kernel/ontology/relations.py:8` | `[a-z][a-z0-9_-]*` (con `fullmatch`) | ❌ | `Relation(kind="clinic.has_appointment")` lanza `ValidationError` |

**Efecto:** la misma cadena es válida o inválida según el nivel que la evalúe.
`tests/kernel/test_ontology_bundle.py:50` usa `relation_kinds={"clinic.has_appointment"}` como
ejemplo **válido** para `validate_against_metamodel`, mientras que el modelo `Relation` de
instancia rechazaría ese mismo `kind`. La nota de `vocabulary.py:23-25` aclara que el `Vocabulary`
no impone el regex (por `EVENT_VOCAB` en PascalCase), lo que deja **tres** convenciones de nombre
conviviendo: canónica con `.`, relación sin `.`, y eventos en PascalCase.

### AUD-15 — 🟡 Tres representaciones de `Action` y dos de `ExecutionResult`

**Real:**

| Modelo | Archivo | Forma | ¿Lo usa el `Executor`? |
|---|---|---|---|
| `Action` estricto | `contracts/execution.py:51-91` | `tenant_id`, `ActionParams` tipado, `status`, `extra=forbid` | ❌ |
| `Action` laxo | `execution/action.py:7-14` | `params: dict`, sin `tenant_id`, sin `extra=forbid` | ✅ (`executor.py:6`) |
| "acción" como string | `execution/executor.py:186-197` | `execute(action: str, params: dict, …)` | ✅ (API real) |
| `ExecutionResult` estricto | `contracts/execution.py:145-164` | `output_keys: List[str]` ("nunca valores: no filtrar datos") | ❌ |
| `ExecutionResult` laxo | `execution/result.py:5-11` | `output: dict` | ✅ (`executor.py:7`) |

Además, `Executor.execute()` **no devuelve** ninguna de las dos clases: retorna diccionarios planos
(`{"success": …, "output": output}`, `executor.py:385-388`).

**Consecuencia concreta:** la garantía declarada en `contracts/execution.py:157-160` ("claves de
salida, **nunca valores**: no filtrar datos") **no se aplica al camino real**. La redacción de
secretos existe y se aplica a los **errores** (`_safe_error` con `_SECRET_PATTERNS`,
`executor.py:15-59`), pero `output` se devuelve sin sanear (`executor.py:387`).

### AUD-16 — 🟡 `Executor.execute_action()` ignora el tenant del contexto

**Real:** `execution/executor.py:413-429` (`execute_action`) llama a `execute()` con
`tenant_id="system"` **fijo**.

Esto contrasta con el camino principal, que aplica correctamente la regla contraria: `execute()`
deriva el tenant del contexto (`executor.py:201-204`, `_tenant_from_context` en `101-131`) y
**rechaza** que el `params["tenant_id"]` difiera (`executor.py:311-332`, con auditoría
`ActionDenied`). Es decir, el mismo ejecutor contiene una versión estricta y otra laxa de la misma
invariante de aislamiento.

Consecuencia adicional: al ir con `tenant_id="system"`, la decisión se resuelve contra
`data/policies/system.json` —archivo que no está presente en `data/policies/`
(solo existen `agentic-compiler.json` y `bor-agencia.json`)—, de modo que cae en
`default_policy("system")`. Con `DEV_ALLOW_ALL=false` eso es deny; con `DEV_ALLOW_ALL=true`
es `allow` (ver AUD-11).

### AUD-17 — 🟡 Los números del catálogo de conectores están desactualizados

**Declarado:** `README.md:121-124` y `README.md:132-137` ("Los 44 providers", "**44 providers · 265 mappings
provider-capability · ~187 capabilities canónicas únicas**", "**44 conectores** declarados"), y
`CHANGELOG.md:30` ("Connector Kernel con 44 providers declarados (stub)").

**Real (medido sobre `src/agentic_os/connectors/providers/*.py`):**

| Métrica | Documentado | Medido |
|---|---|---|
| Claves `connector_id` declaradas | 44 | **45** |
| Mappings provider→capability (`"caps": [...]`) | 265 | **286** |
| Capabilities canónicas únicas | ~187 | **203** |

Desglose por archivo: `__init__.py` 8, `catalog_ai_web.py` 7, `catalog_comms_social.py` 8,
`catalog_content_ops.py` 8, `catalog_data_voice.py` 14 → 45 en total.

**Nota positiva verificada:** los 45 `connector_id` son **únicos** (0 colisiones entre el diccionario
base y los 4 catálogos), por lo que el encadenado `PROVIDER_SPECS.update(...)`
(`providers/__init__.py:109-112`) no sobreescribe ninguna entrada hoy. Ese encadenado, sin embargo,
**no comprueba colisiones** —a diferencia de la ontología, que sí rechaza colisiones contra
`DEFAULT_VOCAB` (`validator.py:129-145`)—: una futura entrada duplicada sobrescribiría en silencio.

### AUD-18 — 🟡 `tests/bugs/` no existe, pero se cita como requisito bloqueante de merge

**Real:** `tests/bugs/` no existe en el repositorio. Los 22 tests de regresión viven en
`tests/agent-notes/bugs/` (`test_bug1_ssrf.py` … `test_bug20_toolregistry_falla_silencioso.py`).
Sin embargo:

| Documento/línea | Referencia |
|---|---|
| `docs/INVARIANTS.md:20` | "**Tests**: `tests/bugs/test_bug5_devallowall.py`, …" (sección Policy) |
| `docs/GOVERNANCE.md:41` | "Tests de policy: `tests/bugs/test_bugNN_*.py`" |
| `Makefile:38` (`test-kernel`) | `python -m pytest tests/kernel/ tests/bugs/ -q` |
| `CONTRIBUTING.md` | instruye crear regresiones en `tests/bugs/test_bugNN_<descripcion>.py` |

**Efecto:** la documentación de gobernanza apunta a una ruta inexistente, y el target `make
test-kernel` —descrito como "Tests del kernel (invariantes)"— no puede ejecutarse tal cual. La
huella de gobernanza (qué test protege qué invariante) queda desalineada de dónde viven realmente
los tests.

### AUD-19 — 🟡 `scripts/audit.sh` no puede pasar en verde

**Real:** el script se presenta como "Repo Health Audit (12 checks)" y como `make audit`. Tres
problemas verificables:

| Check | Línea | Problema |
|---|---|---|
| 4 — "`test_google_*` fuera de `tests/`" | `audit.sh:42-43` | Falla: existen `tests/test_google_connectors.py` y `tests/test_google_real_routing.py` (hay además versiones en `tests/manual/`) |
| 7 — "`EventLog.append()`" | `audit.sh:54` | Falla: importa `agentic_os.kernel.world.event_log`, **módulo que no existe** (el real es `kernel/world/events.py`, exportado por `kernel/world/__init__.py:1`) |
| 5 — "pytest config coherent" | `audit.sh:46` | No puede fallar por construcción: la comprobación termina en `|| true` |

Los checks 1 (`pip install --dry-run -r requirements.txt`) y los de docs (10/11/12) sí son
comprobaciones reales, aunque dependen de red y son de existencia de ficheros.

**Efecto:** la verificación de higiene declarada en el Makefile y en `CONTRIBUTING.md` no es una
señal fiable: hoy está roja por dos motivos independientes, uno de ellos porque referencia código
que ya no existe. *Pendiente de confirmar en runtime* (no se ejecutó `bash scripts/audit.sh`).

### AUD-22 — 🟡 Estado de runtime versionado en git (`data/policies/*.json`)

**Real:** `.gitignore:15-27` abre una sección explícita ("Runtime state — NUNCA commitear") que
ignora `data/tenants/*.json`, `data/conversations/`, `data/eventlog/`, `data/agents/…`,
`data/idempotency/`, `data/creds/` y `src/data/` — pero **no menciona `data/policies/`**.

Comprobado en el repositorio:

| Evidencia | Resultado |
|---|---|
| Archivos bajo `data/policies/` | `agentic-compiler.json`, `bor-agencia.json` |
| Están trackeados | **Sí** (aparecen en `git ls-files`; el `git status` los muestra como `M`, no como `??`) |
| Estado al inicio de esta auditoría | árbol limpio |
| Estado al cierre | `data/policies/bor-agencia.json` como ` M`; `git diff --numstat` → **277 inserciones / 1 borrado** |

**Efecto:** el artefacto que consume `PolicyEngine._load_policy()` (`engine.py:83-95`) —las reglas de
autorización efectivas de un tenant— vive en el historial de git, y cada ejecución local de la
aplicación ensucia el árbol de trabajo: el estado de runtime se mezcla con cambios de código en
`git diff` y en los PRs. Es la misma categoría de problema que el repositorio ya decidió excluir
para tenants, conversaciones y eventlog.

**Relación con el tooling:** `scripts/audit.sh:37-39` (check 3) sí comprueba que
`data/tenants/registry.json` no esté en git, pero no existe comprobación equivalente para
`data/policies/`.

**Nota de trazabilidad:** esta auditoría no ha escrito en ningún archivo fuera de
`docs/agent-notes/AUDIT_KERNEL_INVARIANTS.md`. El cambio de `bor-agencia.json` (+277 líneas) se
produjo por otro proceso durante la sesión (p. ej. la aplicación en ejecución) y se documenta aquí
únicamente como evidencia del hallazgo.

---

## 5. Hallazgos BAJOS

### AUD-20 — 🔵 Deriva de documentación de estructura y de auditorías previas

| Documento | Declarado | Real |
|---|---|---|
| `README.md:22` y quickstart `README.md:42` | `frontend/` (React + Tailwind, `cd frontend && npm install`) | **`frontend/` no existe**; el frontend es `uniscroll-interface/` (Vite + Tailwind) |
| `README.md:13-24` (bloque de estructura) | 8 paquetes + `frontend/` | 10 paquetes reales: faltan **`agents/`** y **`contracts/`** |
| `README.md:24` | "`tests/` — tests de kernel y llm" | 10 subdirectorios: `agent-notes`, `connectors`, `domains`, `infrastructure`, `interfaces`, `kernel`, `llm`, `manual`, `orchestration`, `security` |
| `docs/agent-notes/13_PERMISSIONS_AUDIT.md:17` | tabla con un método `PolicyEngine.can(capability, resource_kind, roles)` | **ya no existe**: hoy la API es `decide`, `can_for_tenant`, `is_allowed`, `requires_approval`, `request_approval` (`engine.py:102, 187, 202, 216, 222`) |

### AUD-21 — 🔵 Higiene: artefactos en limbo, duplicados y un hueco en `.gitignore`

| Elemento | Estado verificado |
|---|---|
| `data/tenants/bor-agencia/drafts/drf_80136194da.json` | Aparece como **untracked** (`??`): `.gitignore` tiene `data/tenants/*.json`, que **no cubre subcarpetas** (`drafts/`, `artifacts/`, `chat/`, `drive/` que el propio código escribe) |
| `pytest_final.txt` | untracked en la raíz |
| `_cognition_diff.txt`, `.env.example.example`, `.coverage` | restos en la raíz (los dos primeros no están cubiertos por `.gitignore`) |
| `src/agentic_os/domains/_examples/__init__.py.py` | archivo basura junto a `__init__.py` |
| `scripts/Agent-Lock (1).py`, `docs/agent-notes/scripts/PROMPTS-AGENTES (2).md` | duplicados con sufijo `(n)` |
| `scripts/__pycache__/Executor.cpython-312.pyc`, `tests/domains/__pycache__/test_projections.cpython-312/314-pytest-9.1.1.pyc` | pycache **huérfanos**: sus fuentes no existen |
| `docs/archive/` | `run_adapter_tests.py`, `run_conn_tests.py`, `run_tests_v2.py`, `_probe_im.py` + 8 dumps `test_*_result.txt` |

**Impacto del hueco de `.gitignore`:** es el hallazgo con consecuencia práctica real (un `git add .`
podría incluir datos de runtime de un tenant). El resto es ruido de higiene que degrada la lectura
del repo y los `__pycache__` de dos intérpretes distintos (`cpython-312` y `cpython-314`) mezclados
en el mismo árbol.

---

## 6. Cobertura real de las invariantes declaradas

Contraste de cada invariante de `docs/INVARIANTS.md` (y de los principios de `README.md`) con el
código. Escala: ✅ cumple · 🟨 cumple parcialmente / con salvedades · ❌ no cumple.

| Invariante declarada | Fuente | Estado | Detalle |
|---|---|---|---|
| `Event immutable` | `INVARIANTS.md:10` | ✅ | `Event` es `KernelModel` frozen (`types/__init__.py:17-22`, `world/events.py:39`) |
| `Log append-only` | `INVARIANTS.md:11` | 🟨 | `append()` respeta lock y validación, pero `events` es público y mutable → AUD-07 |
| `State derivable` | `INVARIANTS.md:12` | 🟨 | Replay determinista para los 4 `kind` reconocidos; los demás se descartan en silencio → AUD-04/05 |
| `apply pure` | `INVARIANTS.md:13` | ✅ | No muta el estado previo; probado (`test_worldstate_typed.py:128-137`) |
| `version +1 per event` | `INVARIANTS.md:14` | ✅ | `applier.py:74-76`; es justamente el mecanismo que hace invisible AUD-04 |
| `CorruptEventError` (nunca estado parcial) | `INVARIANTS.md:15` | 🟨 | Se lanza correctamente con índice; solo cubre los 4 `kind` reconocidos → AUD-04 |
| `Policy immutable` | `INVARIANTS.md:22` | ✅ | `Policy`/`PolicyRule` frozen (`policy/models.py:5-17`) |
| `Deny by default` | `INVARIANTS.md:23` | 🟨 | El evaluador deniega sin regla (`evaluator.py:62`); `DEV_ALLOW_ALL` corta antes → AUD-11 |
| `Approval != granted` | `INVARIANTS.md:24` | 🟨 | `Executor` no ejecuta en `require_approval` (`executor.py:261-280`); el cortocircuito dev anula el caso → AUD-11 |
| `Engine pure` | `INVARIANTS.md:25` | ❌ | I/O de disco y dependencia de CWD → AUD-02 |
| `Delete/Publish → approval` | `INVARIANTS.md:26` | 🟨 | Correcto en `PolicyEvaluator`; bypassable con `DEV_ALLOW_ALL` → AUD-11 |
| `is_canonical_kind` | `INVARIANTS.md:33` | 🟨 | Correcto en `vocabulary.py`, discrepante con `relations.py` → AUD-14 |
| `DEFAULT_VOCAB` inmutable en runtime | `INVARIANTS.md:34` | ❌ | `set` mutable pese a `frozen`; comprobado en runtime → AUD-08 |
| Dominio extiende con namespace, nunca colisiona | `INVARIANTS.md:35` | 🟨 | Garantizado en `validate_against_metamodel` (probado), pero sin efecto en runtime → AUD-09 |
| `validate_against_metamodel` falla-closed | `INVARIANTS.md:36` | ✅ | Rechaza no canónico, colisión y refs rotas agregando errores (`validator.py:118-164`); probado en `test_ontology_bundle.py:62-81` |
| `ENTITY_TYPE_REGISTRY` arranca vacío en import (I5) | `domain_models.py:14-16` | ✅ | `test_kernel_registry_starts_empty.py`; salvedad de scope global → AUD-10 |
| "Kernel = invariantes" / kernel no importa dominios | `README.md:3`, `CONTRIBUTING.md` | ❌ | Import a `infrastructure` desde `policy/engine.py:73` y test ciego → AUD-01 |
| "Policy gobierna Capability, no el agente" | `README.md:7` | 🟨 | Cierto salvo el gate de entorno → AUD-11 |
| "Clasificación de riesgo por capability" | `README.md` (conectores) | ❌ | Solo `delete`/`publish` → AUD-13 |

## 7. Evidencia reproducible

Comprobaciones **ejecutadas** con el intérprete global (`Python 3.12.10`) fuera del árbol del
repositorio, para no generar `__pycache__` ni artefactos en el repo.

**Prueba 1 — el test de capas es ciego a imports relativos**

```python
import ast
src = "from ...infrastructure.tenancy import TenantRegistry"
for node in ast.walk(ast.parse(src)):
    if isinstance(node, ast.ImportFrom):
        print("node.module =", repr(node.module), "| node.level =", node.level)
        print("startswith(agentic_os.infrastructure) ->",
              node.module.startswith("agentic_os.infrastructure"))
```

```
node.module = 'infrastructure.tenancy' | node.level = 3
startswith(agentic_os.infrastructure) -> False
```

**Prueba 2 — `frozen=True` no protege los `set` internos**

```python
from pydantic import BaseModel, ConfigDict

class V(BaseModel):
    model_config = ConfigDict(frozen=True)
    entities: set = {"actor"}

v = V()
v.entities.add("evil.injected")   # muta el set
print(sorted(v.entities))
try:
    v.entities = {"otro"}         # reasignación
except Exception as e:
    print("reasignacion bloqueada:", type(e).__name__)
```

```
['actor', 'evil.injected']
reasignacion bloqueada: ValidationError
```

**Mediciones textuales** (regex sobre los archivos, sin importar el paquete):
conteo de `"connector_id"` y de elementos de `"caps"` en `connectors/providers/*.py` (AUD-17);
conteo de `kind=` / `event_type=` en `src/agentic_os/**` y contraste con `EVENT_VOCAB` (AUD-05/06),
verificando después cada sitio por lectura del código.

## 8. Límites del informe y comprobaciones pendientes de runtime

**No ejecutado** (fuera del alcance de este documento): `pytest`, `ruff`, `mypy` y
`bash scripts/audit.sh`. Quedan por confirmar en runtime:

1. Si la suite completa pasa hoy en este estado del repo (y, por tanto, si AUD-18 y AUD-19 afectan
   solo al `Makefile`/documentación o también a la CI).
2. La ejecución real de `bash scripts/audit.sh` y el recuento de checks rojos (AUD-19).
3. `make test-kernel`, cuyo segundo `testpath` apunta a `tests/bugs/` (AUD-18).

**Contexto de entorno que condiciona cualquier medición de tests** (no medido en este informe):

| Entorno | Python | Nota |
|---|---|---|
| intérprete global usado para las pruebas de §7 | 3.12.10 | fuera del repo, sin escribir en él |
| `.venv` del repositorio | 3.14.7 | `pyvenv.cfg` |
| CI (`.github/workflows/ci.yml`) | 3.11 | incluye `--cov-fail-under=70` y escaneo gitleaks que este informe no evalúa |

El árbol contiene `__pycache__` de **dos** versiones (`cpython-312` y `cpython-314`), señal de que se
han ejecutado tests con al menos dos intérpretes distintos. Un resultado verde en `.venv` (3.14) no
es trasladable sin más a la CI (3.11).

**Fuera de alcance de esta auditoría:** `cognition/`, `orchestration/` e `interfaces/` (salvo los
usos citados como evidencia), `infrastructure/` (salvo `config/settings.py` y `tenancy/`), el
frontend (`uniscroll-interface/`) y el comportamiento funcional de los 45 providers del catálogo
(declarados como stubs no conectados).

**Naturaleza del documento:** diagnóstico y severidad, según lo solicitado. No contiene propuestas
de cambio de código ni plan de remediación.
