# MINIPROMPTS UNIFICADOS PARA CLINE — agentic-os

Este documento sustituye a `PLAN_IMPLEMENTACION_CLINE_V2.md` y a
`AUDITORIA_REAL_PENDIENTES.md`. Está verificado contra el repodump real
(`uniscrolliabrain-cloud-agentic-os`), no contra suposiciones. Cada bloque
indica primero **qué ya existe en el repo** (para no repetir trabajo) y
luego los miniprompts pendientes, en piezas pequeñas para que Cline no se
pierda ni mezcle versiones.

Asunción: `ontology_prompt_finalv3.md` sigue disponible en el workspace de
Cline (los miniprompts de los Bloques F, B, C y D referencian líneas suyas,
igual que hacía el plan v2). Si no está, dímelo y te doy el código inline
en vez de la referencia por línea.

---

## 0. AUDITORÍA REAL — qué ya está hecho

| Bloque | Estado real en el repo |
|---|---|
| **A1–A8** (entidades tipadas, WorldState, applier, replay) | ✅ **YA IMPLEMENTADO** en `kernel/ontology/domain_models.py`, `kernel/world/state.py`, `kernel/world/applier.py`, `kernel/world/replay.py`. Las 9 entidades, `ENTITY_TYPE_REGISTRY`, `EntityUnion` discriminado por `kind`, y el fail-closed de `apply()`/`replay()` existen y tienen tests (`tests/domains/test_domain_entity.py`, `tests/domains/test_entity_registry.py`, `tests/kernel/test_worldstate_typed.py`). **No los toques.** |
| **A9** (migrar pipelines a entidades tipadas) | ✅ **YA IMPLEMENTADO** — `PipelineRunner.emit_event()` emite `entity_created` al EventLog. `pipeline_leads_to_draft.py` crea entidades `Lead` (fail-closed con ValidationError) y `pipeline_daily_social.py` crea `BlogPost` (fail-closed). Tests en `tests/automation/test_pipeline_leads_typed.py` (A9.1 + A9.2). **No los toques.** |
| **A10** (gate) | Pendiente correr y pegar salida una vez cerrado A9. |
| **Bloque F** (contratos Skill/Pipeline/MiniAgent) | ❌ No existe `src/agentic_os/contracts/` en el repo. Ni una clase. Empezar desde cero. |
| **Bloque B** (SMC) | ❌ No existe `cognition/reasoning/smc.py`. Sí existe `cognition/reasoning/proposer.py` — revisar antes de crear el nuevo archivo por si hay que fusionar. |
| **Bloque C** (Model Router) | ❌ No existe `interfaces/llm/router.py`. **Pero `GeminiProvider`, `GroqProvider`, `FallbackLLMProvider` y `MockLLMProvider` YA EXISTEN** en `interfaces/llm/provider.py` — el router los importa, no los reimplementa. `Settings` tampoco tiene aún `llm_router_parallel_enabled`. |
| **Bloque D** (identidad JWT) | ❌ No existe `src/agentic_os/identity/`. Empezar desde cero. Ojo: `interfaces/api/deps.py` ya existe con su propio mecanismo (`tenant_scope`/`admin_scope`) y tiene tests reales en `tests/security/` — no tocarlo, JWT va en paralelo. |
| **Bloque E** (credenciales) | ⚠️ **A medias, y no como dice el plan v2.** Ya existe `connectors/auth/credential_store.py` con `CredentialStore` + `EncodedFileCredentialStore` cifrando con Fernet — **no es el `CredentialStore` base64 que describía el plan anterior**, alguien ya lo mejoró. Pero **no es fail-closed**: si falta `CREDENTIAL_ENCRYPTION_KEY` genera una clave aleatoria por proceso y solo *avisa* con un `logger.warning`, no falla. Tampoco usa escritura atómica (`tmp_path` + `os.replace`) — usa `open(path, "w")` directo. Hay tests reales en `tests/security/test_credential_store.py` que **debes mantener en verde** (aislamiento por tenant, roundtrip de `SecretStr`, credencial malformada no crashea). |
| **CORS / branqueo frontend Uniscroll** | Es otro documento (`CLINE_PROMPTS...branqueo`) ya presente en el repo, **no se solapa con este plan** — son prompts de infraestructura del frontend Vite/React, no ontología. Ignóralo para este plan. |

Orden de ejecución recomendado (actualizado contra la auditoría real):

```
A9 → A10 (cerrar Bloque A)
  → E1-E3 (Bloque E, es el más pequeño y aislado)
  → F1-F7 (Bloque F, lo necesita B)
  → D1-D4 (Bloque D, independiente, en paralelo si quieres)
  → C1-C4 (Bloque C, lo necesita B)
  → B1-B5 (Bloque B, cierra con C ya construido)
```

---

## BLOQUE A — CIERRE (A9, A10)

### A9.1 — Migrar `pipeline_leads_to_draft.py`
```
Contexto: el pipeline ya funciona (lee leads de Drive, genera borrador con
LLM, llama a gmail_create_draft). Falta que cada lead procesado quede
también como entidad tipada en el WorldState, no solo como borrador de
Gmail.

Archivo: src/agentic_os/orchestration/pipelines/pipeline_leads_to_draft.py

Tarea:
1. Importa Lead desde agentic_os.kernel.ontology.domain_models.
2. Importa la función/mecanismo que ya use el runner para emitir eventos al
   EventLog (busca cómo lo hacen otros sitios que llaman a runner.tool() —
   normalmente hay un runner.emit_event() o similar; si no existe, revisa
   orchestration/pipelines/runner.py y dime qué encontraste antes de
   inventar una interfaz nueva).
3. Por cada lead parseado en _parse_leads(), antes de crear el draft,
   construye un Lead(tenant_id=tenant_id, name=..., email=..., source="import")
   y emite un evento entity_created con ese payload (usa entity.model_dump()
   como payload, entity.id como entity_id del evento).
4. Si Lead(...) lanza ValidationError (email inválido, etc.), captura la
   excepción, NO crees el draft para ese lead, y añade el error a una lista
   `errors` que se devuelve en el resultado final junto a `drafts_created`.

No cambies la lógica de generación de emails ni el flujo de gmail_create_draft.

Criterio de aceptación: test nuevo en tests/automation/test_pipelines.py
(o archivo nuevo tests/automation/test_pipeline_leads_typed.py) que:
(a) corre el pipeline con 2 leads válidos + 1 con email inválido,
(b) comprueba que el WorldState resultante tiene 2 entidades Lead,
(c) comprueba que el resultado incluye 1 entrada en `errors`,
(d) comprueba que solo se crearon 2 drafts (no 3).
Pega la salida de pytest.
```

### A9.2 — Migrar `pipeline_daily_social.py`
```
Contexto: mismo patrón que A9.1 pero con BlogPost/contenido publicado.

Archivo: src/agentic_os/orchestration/pipelines/pipeline_daily_social.py

Tarea:
1. Importa BlogPost desde domain_models.
2. Cuando se genera el `copy` final (antes de llamar a meta_post_publish),
   crea un BlogPost(tenant_id=tenant_id, title=candidate["name"], body=copy)
   y emítelo como entity_created, igual que en A9.1.
3. Si BlogPost(...) falla validación (título vacío, etc.), no publiques
   (no llames a meta_post_publish) y devuelve status="VALIDATION_ERROR"
   con el detalle del error de Pydantic.

Criterio: test que fuerza un candidate con name="" (título vacío) y
comprueba que status == "VALIDATION_ERROR" y que meta_post_publish NUNCA
se llamó (mockea runner.tool y comprueba que no se invocó con
"meta_post_publish"). Pega salida de pytest.
```

### A9.3 — Migrar `pipeline_inbox_watcher.py`
```
Contexto: revisa primero el contenido actual del archivo (no lo tengo
resumido aquí) y aplica el mismo patrón: identifica qué entidad de las 9
tipadas (probablemente Lead si detecta un email nuevo, o ninguna si solo
reenvía/etiqueta) encaja con lo que hace este pipeline, y emite
entity_created para ella siguiendo exactamente el mismo patrón de A9.1/A9.2.

Si el pipeline no crea ningún dato que encaje con las 9 entidades del
Bloque A (por ejemplo si solo mueve o clasifica correos sin generar un
Lead ni nada del dominio), dilo explícitamente en tu respuesta y NO fuerces
una entidad que no aplica — deja el pipeline igual y explica por qué.

Criterio: si aplica cambio, mismo patrón de test que A9.1/A9.2. Si no
aplica, entrega una explicación de 3-4 líneas de por qué este pipeline no
tiene una entidad tipada que emitir.
```

### A10 — Gate del Bloque A
```
Tarea: correr:
pytest tests/kernel/ tests/domains/ tests/automation/ -q

Pega la salida completa y literal. Si algo falla, no lo arregles todavía
sin decírmelo primero — dime qué test falla y por qué antes de tocar código
de producción para "hacerlo pasar".
```

---

## BLOQUE E — CREDENCIALES (fail-closed + escritura atómica)

No sustituyas `CredentialStore` por una clase nueva desde cero — ya tiene
tests en verde que hay que preservar. Es un parche quirúrgico, no un swap.

### E1 — Fail-closed si falta `CREDENTIAL_ENCRYPTION_KEY`
```
Archivo: src/agentic_os/connectors/auth/credential_store.py

Contexto: hoy _fernet() genera una clave aleatoria por proceso y solo
avisa con logger.warning si falta CREDENTIAL_ENCRYPTION_KEY. Eso permite
arrancar en modo degradado (las credenciales guardadas no se podrán leer
tras un reinicio, y el usuario no se entera hasta que falla en producción).

Tarea:
1. Crea la excepción SecurityConfigurationError(RuntimeError) en el mismo
   archivo (o impórtala si ya existe una equivalente en
   connectors/core/errors.py — revisa primero y usa esa si existe).
2. En _fernet(), si no hay raw_key (ni en settings ni en el entorno),
   NO generes una clave aleatoria: lanza SecurityConfigurationError con un
   mensaje claro ("CREDENTIAL_ENCRYPTION_KEY no configurada; no se puede
   inicializar el almacén de credenciales").
3. Añade un flag explícito de opt-out SOLO para tests/dev, por ejemplo
   permitir que CredentialStore.__init__ reciba allow_ephemeral_key: bool =
   False, y solo si es True se permite la clave aleatoria de antes (con el
   mismo warning). El comportamiento por defecto (como lo usa el resto del
   código, sin ese flag) debe ser fail-closed.

No cambies la firma pública de save()/load()/delete().

Criterio: test nuevo en tests/security/test_credential_store.py:
- test_falla_sin_encryption_key_por_defecto: sin CREDENTIAL_ENCRYPTION_KEY
  en el entorno y sin allow_ephemeral_key, instanciar CredentialStore y
  llamar a save() debe lanzar SecurityConfigurationError.
- test_permite_clave_efimera_explicita: con allow_ephemeral_key=True,
  save()/load() funcionan igual que antes (no rompas los tests existentes).
Pega salida de: pytest tests/security/test_credential_store.py -q
```

### E2 — Escritura atómica
```
Archivo: src/agentic_os/connectors/auth/credential_store.py

Tarea: en CredentialStore.save(), sustituye:
    with open(path, "w") as f:
        json.dump(data, f)
por escritura a un fichero temporal en el mismo directorio + os.replace():
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with open(tmp_path, "w") as f:
        json.dump(data, f)
    tmp_path.chmod(0o600)  # antes del replace, mismo best-effort que ya hay
    os.replace(tmp_path, path)

Esto evita dejar un fichero de credenciales corrupto/truncado si el proceso
muere a mitad de escritura. Mantén el chmod(0o600) existente.

Criterio: test que parchea json.dump para que lance una excepción a mitad
de la escritura y comprueba que el fichero original (si existía) queda
intacto y que no queda ningún .tmp huérfano tras la excepción (usa un
finally o comprueba con os.listdir). Pega salida de pytest.
```

### E3 — Gate del Bloque E
```
pytest tests/security/test_credential_store.py tests/bugs/test_bug3_credentialstore.py -q
Pega salida completa. Todos los tests previos deben seguir en verde además
de los nuevos de E1/E2.
```

---

## BLOQUE F — CONTRATOS (Skill / Pipeline / MiniAgent)

Fuente: `ontology_prompt_finalv3.md`, líneas 260-538 (PARTE II completa).
Archivo destino: `src/agentic_os/contracts/core.py` (nuevo — crea también
`src/agentic_os/contracts/__init__.py` vacío).

Bug a corregir en el camino (ver auditoría del plan v2, sigue vigente):
`ExecutionTask.created_at` debe usar `default_factory=now_utc` (importado
de `agentic_os.kernel.types.time`), nunca `datetime.utcnow`.

### F1 — Contratos de entrada/salida
```
Archivo: src/agentic_os/contracts/core.py (nuevo)

Tarea: implementa, tomando el código de ontology_prompt_finalv3.md líneas
260-538, exactamente estas clases (sin las de skill/pipeline/agente
todavía, eso va en F2-F6): InputField, OutputField, InputContract,
OutputContract.

Usa BaseModel de Pydantic v2 con la misma config estricta que ya usa
domain_models.py (frozen=True, extra="forbid") salvo que el documento de
referencia especifique otra cosa explícitamente para estas clases — si hay
conflicto entre "config estricta consistente" y "lo que dice el
documento", para y pregunta, no decidas tú.

Criterio: test en tests/contracts/test_core_contracts.py que instancia un
InputContract con un InputField y comprueba que falla con ValidationError
si le pasas un campo extra no declarado (extra="forbid").
```

### F2 — Capabilities
```
Archivo: src/agentic_os/contracts/core.py (append)

Tarea: implementa CapabilityConstraint, CapabilityPermission, Capability
de las mismas líneas 260-538 del documento de referencia.

Criterio: test que instancia una Capability con una CapabilityPermission
inválida (fuera de los valores permitidos que defina el documento) y
comprueba ValidationError.
```

### F3 — Skill
```
Archivo: src/agentic_os/contracts/core.py (append)

Tarea: implementa SkillInputMapping, SkillOutputMapping, SkillPrecondition,
SkillPostcondition, Skill.

Criterio: test que arma un Skill mínimo válido (con al menos un
InputContract y un OutputContract de F1) y uno inválido (sin
input_contract) y comprueba que el segundo falla.
```

### F4 — SkillGraph
```
Archivo: src/agentic_os/contracts/core.py (append)

Tarea: implementa SkillDependency, SkillGraph con su método
validate_graph().

Tests obligatorios (dos, no uno):
1. Un SkillGraph con entry_skill que no existe en la lista de skills →
   validate_graph() debe fallar (lanzar la excepción que defina el
   documento, o ValueError si no especifica una propia).
2. Una skill que depende de sí misma (self-loop en SkillDependency) →
   validate_graph() debe fallar también.
Pega salida de pytest con ambos tests.
```

### F5 — Pipeline
```
Archivo: src/agentic_os/contracts/core.py (append)

Tarea: implementa SOPStep, PipelineNode, PipelineEdge, Pipeline (con su
propio validate_graph()).

Mismo patrón de test que F4: un Pipeline con self-loop entre dos
PipelineNode debe ser rechazado explícitamente por validate_graph().
```

### F6 — MiniAgent
```
Archivo: src/agentic_os/contracts/core.py (append)

Tarea: implementa AgentPermission, AgentLimit, AgentFailurePolicy,
MiniAgent.

Gate específico de este paso: test que arma un MiniAgent con
failure_policies y comprueba que AgentFailurePolicy.action solo acepta
retry|fallback|stop|escalate|rollback|ignore vía el patrón regex de
Pydantic — instanciar con "otro_valor" debe fallar en la validación del
modelo (ValidationError), no más tarde en tiempo de ejecución.
```

### F7 — ExecutionTask y AgentExecutionPlan (con el bug corregido)
```
Archivo: src/agentic_os/contracts/core.py (append)

Tarea: implementa ExecutionTask y AgentExecutionPlan. Para ExecutionTask,
el campo created_at debe ser:
    from ..kernel.types.time import now_utc
    created_at: datetime = Field(default_factory=now_utc)
NUNCA datetime.utcnow — comprueba que el import está arriba del archivo
junto a los demás imports de contracts/core.py, no repetido inline.

Criterio: test que instancia dos ExecutionTask seguidos y comprueba que
created_at es un datetime timezone-aware (si now_utc() devuelve tz-aware,
que es lo que usa el resto del kernel — confírmalo mirando
kernel/types/time.py antes de escribir el test).

Gate final del Bloque F: pytest tests/contracts/ -q con salida completa,
todos los tests de F1-F7 en verde.
```

---

## BLOQUE D — IDENTIDAD JWT (independiente, en paralelo si quieres)

### D1 — Paquete base
```
Tarea: crea el paquete nuevo:
- src/agentic_os/identity/__init__.py (vacío)
- src/agentic_os/identity/models.py → UserContext(BaseModel): user: str,
  tenant_id: str, roles: list[str]
- src/agentic_os/identity/registry.py → UserRegistry con métodos .get(user_id)
  y .get_service_account(name) — de momento pueden ser stubs deterministas
  en memoria (dict), no hace falta persistencia todavía.

Criterio: test que instancia UserContext con roles=["admin"] y comprueba
los campos; test que UserRegistry().get("no-existe") devuelve None (no
lanza excepción).
```

### D2 — JWT encode/decode
```
Archivo: src/agentic_os/identity/jwt.py (nuevo)

Tarea: añade pyjwt a pyproject.toml (sección [project.dependencies], sigue
el mismo estilo que las demás líneas: "pyjwt>=2.8"). Implementa:
- encode_token(user_context: UserContext, secret: str, expires_in_seconds:
  int = 3600) -> str
- decode_token(token: str, secret: str) -> UserContext, que valida firma Y
  expiración, y lanza una excepción clara (define
  InvalidTokenError(ValueError) en el mismo archivo) si cualquiera de las
  dos falla.

Corrige aquí también el bug del índice de split() que trae el documento de
referencia si lo estás copiando de ontology_prompt_finalv3.md líneas
4206-4276: el token viene de un header "Bearer <token>", así que
authorization.split(" ")[1] es correcto SOLO si compruebas antes que
len(authorization.split(" ")) == 2 — si no, devuelve 401 en vez de dejar
que explote con IndexError.

Test obligatorio (Invariante 18): un JWT válido con roles: ["admin"]
modificado a mano en el payload (firma no recalculada, es decir, cambias
el payload en base64 pero dejas la firma original) debe ser rechazado por
decode_token() — no vale solo con que expire. Escribe este test
construyendo el token manualmente (encode, decodificar el JSON del
payload, cambiarlo, re-encodear en base64 sin volver a firmar) para
demostrar que decode_token() lo detecta.
```

### D3 — Dependency FastAPI en paralelo (no sustituir deps.py)
```
Archivo: src/agentic_os/interfaces/api/deps.py

Contexto importante: tenant_scope()/admin_scope() ya existen y tienen
tests reales en tests/security/ — NO los toques ni los reemplaces.

Tarea: añade una función NUEVA get_current_user(authorization: str =
Header(None)) -> UserContext como dependency adicional y opcional, que use
decode_token() de D2. No la enganches todavía a ningún endpoint existente
de rest.py — solo debe existir y tener sus propios tests. La decisión de
migrar endpoints uno a uno se toma después, en otro momento, cuando este
mecanismo lleve un tiempo en verde.

Criterio: test que monta un endpoint FastAPI de prueba mínimo (en el mismo
archivo de test, con TestClient) usando Depends(get_current_user), y
comprueba 401 sin header, 401 con header mal formado (sin "Bearer "), y
200 con un token válido generado por encode_token() en el propio test.
```

### D4 — Gate del Bloque D
```
pytest tests/security/ tests/identity/ -q
Pega salida completa: tests/security/ existentes deben seguir en verde +
los nuevos de identity/ en verde.
```

---

## BLOQUE C — MODEL ROUTER

`GeminiProvider`, `GroqProvider`, `FallbackLLMProvider`, `MockLLMProvider`
ya existen en `interfaces/llm/provider.py` — el router los importa, nunca
duplica su lógica.

### C1 — Settings + esqueleto del router
```
Archivo 1: src/agentic_os/infrastructure/config/settings.py
Tarea: añade el campo llm_router_parallel_enabled: bool = False a la clase
Settings (confirma primero que no existe ya con otro nombre parecido antes
de añadirlo duplicado).

Archivo 2: src/agentic_os/interfaces/llm/router.py (nuevo)
Tarea: implementa ModelRouter.__init__ y _initialize_providers() (tomando
como referencia ontology_prompt_finalv3.md líneas 4116-4204, la segunda
aparición). _initialize_providers() debe:
- leer settings para saber qué API keys hay disponibles
- importar GeminiProvider y GroqProvider de interfaces/llm/provider.py
  (import, nunca copiar su código)
- si ninguna key está configurada, caer a MockLLMProvider como único
  provider (no debe explotar por falta de keys)

Criterio: test que instancia ModelRouter con settings mockeadas sin
ninguna API key y comprueba que termina usando solo MockLLMProvider, sin
lanzar excepción.
```

### C2 — route_structured (modo síncrono)
```
Archivo: src/agentic_os/interfaces/llm/router.py

Tarea: implementa route_structured() con el switch entre modo paralelo (si
settings.llm_router_parallel_enabled) y modo síncrono simple (primer
provider disponible, sin paralelismo). Implementa primero solo la rama
síncrona en este paso.

Criterio: test con llm_router_parallel_enabled=False y 2 providers
mockeados (uno que responde OK) — comprueba que solo se llama al primero
en el orden de prioridad, no al segundo.
```

### C3 — Modo paralelo con cancelación
```
Archivo: src/agentic_os/interfaces/llm/router.py

Tarea: implementa _route_parallel_structured(), tomando como referencia
ontology_prompt_finalv3.md línea 4160 en adelante (la versión que SÍ
cancela tareas perdedoras con p.cancel() — evita la versión de la línea
691-732 del mismo documento, que no cancela y desperdicia cuota de API).

Gate de este paso (obligatorio, no opcional): test que mockea 2 providers,
uno lento (asyncio.sleep largo) y uno rápido que lanza una excepción de
validación, y comprueba las 3 cosas:
(a) gana el que responde válido primero (si hay un tercero rápido y
    válido, o si reformulas el test con un lento+válido vs un
    rápido+inválido, el ganador debe ser el válido, sea cual sea su
    velocidad relativa al que falla),
(b) la tarea del provider lento queda efectivamente cancelada (comprueba
    con task.cancelled() o equivalente, no solo que "no se usó su
    resultado"),
(c) si TODOS los providers fallan, route_structured() propaga la última
    excepción, no una genérica.
```

### C4 — Auditoría + gate final
```
Archivo: src/agentic_os/interfaces/llm/router.py

Tarea: cada llamada a route_structured() debe generar un Event en el
EventLog con qué provider ganó y cuáles fallaron. Esto NO está en el
documento de referencia — síguelo el patrón que ya use Executor._audit()
en execution/executor.py (revísalo primero, cópialo en estilo, no
inventes un formato de evento nuevo).

Gate del Bloque C completo:
pytest tests/llm/ -q (incluyendo los tests nuevos de C1-C4)
Pega salida completa.
```

---

## BLOQUE B — SMC (Semantic Mission Compiler)

Antes de crear el archivo nuevo: abre `cognition/reasoning/proposer.py` y
dime en tu respuesta si ya hace algo equivalente a `Classifier` o
`Crystallizer` — si hay solape real, para y pregunta si fusionar en vez de
duplicar. No lo decidas solo.

Fuente: `ontology_prompt_finalv3.md` líneas 1017-1295 (segunda aparición:
`IntentMatch`, `MatchmakingResult`, `Classifier`, `Crystallizer`,
`SemanticCompiler` completos, con el bucle de reintento ante
`ValidationError` — ignora las versiones cortas de las líneas 627-686 y
4054-4115, no tienen el reintento).

Archivo destino: `src/agentic_os/cognition/reasoning/smc.py` (o fusión con
`proposer.py` si el paso anterior lo justifica).

### B1 — Contratos
```
Tarea: implementa IntentMatch, MatchmakingResult.

Criterio: test que instancia MatchmakingResult con un IntentMatch y
comprueba serialización/deserialización básica (model_dump / validate).
```

### B2 — Classifier determinista
```
Tarea: implementa Classifier — debe ser determinista, sin llamar al LLM en
ningún punto (ni siquiera como fallback).

Criterio: test que corre el mismo input dos veces y comprueba que el
resultado es idéntico byte a byte (o campo a campo), y un test que hace
grep del propio archivo del Classifier para confirmar que no importa
ningún provider de interfaces/llm/.
```

### B3 — Crystallizer con reintento
```
Tarea: implementa Crystallizer.crystallize() con el bucle
`for attempt in range(2)` reintentando con los errores de Pydantic
inyectados de vuelta al prompt (línea ~4091 del documento de referencia).
Aquí se usa ModelRouter.route_structured() del Bloque C — si el Bloque C
no está terminado todavía, usa un ModelRouter mock con la interfaz pública
final (route_structured(prompt, output_schema) -> resultado válido o
excepción) y dilo explícitamente en tu respuesta.

Criterio: test que mockea route_structured() para que la primera llamada
devuelva un payload que NO valida contra el schema esperado y la segunda
sí — comprueba que crystallize() reintenta exactamente una vez y devuelve
el resultado válido de la segunda llamada, y que el segundo prompt enviado
incluye el error de validación de la primera (verifica el argumento con
el que se llamó la segunda vez al mock).
```

### B4 — SemanticCompiler
```
Tarea: une Classifier + Crystallizer en SemanticCompiler.

Criterio: test end-to-end con Classifier real + Crystallizer con
ModelRouter mockeado, comprobando que el flujo completo produce un
MatchmakingResult válido.
```

### B5 — Integración en rest.py + gate de invariante
```
Archivo: src/agentic_os/interfaces/api/rest.py
Tarea: engancha SemanticCompiler donde indique ontology_prompt_finalv3.md
línea ~680, sin saltarte PolicyEngine ni Executor (el SMC clasifica y
cristaliza; PolicyEngine y Executor siguen siendo quienes deciden si se
ejecuta algo).

Test de invariante clave (Invariante 12), OBLIGATORIO:
grep -n "tool\.run(\|connector\.execute(" src/agentic_os/cognition/reasoning/smc.py
debe devolver CERO resultados. Si devuelve algo, el Bloque B está mal
implementado — el SMC nunca ejecuta, solo clasifica y cristaliza. Pega la
salida del grep (vacía) como parte del gate.

Gate final: pytest tests/ -q completo (todo el repo), salida pegada.
```

---

## Protocolo de entrega (igual que en el plan anterior)

Para cada miniprompt, Cline debe responder con:
```
STATUS: PASS | FAIL | BLOCKED
ARCHIVOS: <lista de archivos tocados>
CAMBIOS: <resumen de 2-4 líneas>
TESTS: <salida literal de pytest, no un resumen inventado>
```
No se marca nada como PASS sin la salida literal de pytest pegada. Si un
miniprompt requiere una decisión no cubierta aquí (ambigüedad real entre
versiones del documento de referencia, o un archivo que no coincide con lo
que este plan asume que contiene), Cline debe parar y preguntar — no
promediar ni mezclar dos versiones de la misma clase.
