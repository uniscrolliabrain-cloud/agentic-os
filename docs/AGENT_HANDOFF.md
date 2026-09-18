# AGENT_HANDOFF — Cómo trabajamos en este repo

> **Propósito:** este documento explica el MÉTODO de trabajo entre el humano
> (Alfonso) y cualquier agente IA (Claude, GPT, Cline, Aider, etc.). No
> describe QUÉ se hace (para eso está `docs/STATUS.md` + `docs/spec/`), sino
> CÓMO se colabora. Léelo entero antes de ejecutar nada.

---

## 1. Modelo de trabajo

**Un humano + un agente. Punto. No hay equipo, no hay ramas, no hay PRs.**

- El agente **da bloques de PowerShell numerados**. El humano los ejecuta uno
  a uno y **pega el output** de cada bloque.
- El agente **no pide confirmación para cosas obvias**. El humano quiere
  velocidad; solo se pregunta cuando hay una decisión de arquitectura.
- El agente **nunca commitea por su cuenta**. El commit se hace al final de
  un ciclo lógico, y solo si la suite de tests está verde.
- El humano **trabaja sobre `master`**. No hay ramas, no hay PRs. Se decidió
  explícitamente: "es pérdida de tiempo para un humano + un agente".
- El agente **cambia de rama solo si el humano lo pide**. Por defecto: master.

### Loop estándar

1. Agente: "Bloque 1 — Título" + script PowerShell.
2. Humano: pega el output.
3. Agente: valida, corrige, siguiente bloque.
4. Al cerrar el ciclo (3-5 bloques + tests verdes): agente da un bloque
   final que es `git add` + `git commit`.
5. Humano: pega el "commit creado".
6. Agente: actualiza `docs/STATUS.md` si aplica (1 vez por ciclo, no por bloque).

---

## 2. Ciclos de trabajo

El trabajo se organiza en **ciclos**, cada uno con una letra:

| Ciclo | Contenido | Estado |
|---|---|---|
| A | Endurecimiento kernel + endpoints spec (AUD-03, 13, 16, /approvals, /missions) | ✅ cerrado |
| B | Invariantes kernel (AUD-07, 08, 12, 14) | ✅ cerrado |
| C | Observabilidad + contratos (GAP 1/2/3, AUD-15) | pendiente |
| D | Ontología viva (AUD-05, 09, 10) | pendiente |
| E | Specs al día (marcar aspiracional, CHANGELOG) | pendiente |
| F | Higiene del repo (docs/archive, duplicados) | pendiente |

**Un ciclo = 3-5 bloques + 1 commit único.** No commitear entre bloques.

**Excepción:** si un bloque rompe tests por un motivo externo, se puede hacer
un commit parcial solo si el humano lo pide.

---

## 3. Entorno técnico

- **OS:** Windows 10/11.
- **Shell:** PowerShell 5.1 (el de Windows, no PowerShell 7+). Esto importa:
  `Set-Content -Encoding UTF8` escribe **con BOM** y rompe `ast.parse()` de
  Python. Ver "Patrones PowerShell" abajo.
- **Python:** 3.12 global (fuera de venv, o dentro del .venv del repo).
- **Editor:** VS Code.
- **Repo:** `C:\Users\Alfonso\Desktop\git hub repos\agentic-os` (nombre real).
  El repo se llama **`agentic-os`**, no `uniscrolliabrain-cloud-agentic-os`
  (aunque el dump lo llame así).
- **Rama activa:** `master` (SIEMPRE).
- **Git remote:** `origin/master`. Los commits locales van por delante del
  remote hasta que el humano haga `git push`. **Nunca hacer push sin pedirlo.**

---

## 4. Patrones PowerShell

### ✅ Usar esto

**Escribir ficheros sin BOM (crítico para `.py`):**

```powershell
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText((Resolve-Path $path).Path, $contenido, $utf8NoBom)
```

**Generar contenido multilínea (evita here-strings que fallan por CRLF):**

```powershell
$lines = @(
    'linea 1'
    'linea 2'
    'linea 3'
)
$contenido = $lines -join "`n"
```

**Commit con mensaje largo y caracteres raros → siempre `-F`:**

```powershell
$msgPath = "$env:TEMP\commit-msg.txt"
$msg = @"
tipo(scope): descripcion sin tildes

Cuerpo del mensaje.
"@
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($msgPath, $msg, $utf8NoBom)
git commit -F $msgPath
Remove-Item $msgPath
```

**Reemplazo por índice de línea (inmune a tildes, CRLF, espacios raros):**

```powershell
$lines = Get-Content -Path $path
$idx = -1
for ($i = 0; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -match 'patron_buscado') { $idx = $i; break }
}
if ($idx -ge 0) {
    $before = $lines[0..($idx - 1)]
    $after  = $lines[($idx + N)..($lines.Count - 1)]
    # recomponer y escribir sin BOM
}
```

**Python desde PowerShell:**

```powershell
$env:PYTHONPATH = "src"
python -c "from agentic_os... import ..."
Remove-Item Env:\PYTHONPATH
```

**Git log sin paginador (evita que parezca "pillado"):**

```powershell
git --no-pager log -3 --oneline
```

### ❌ NO usar esto

| Anti-patrón | Por qué | Alternativa |
|---|---|---|
| `Set-Content -Encoding UTF8` | Escribe BOM en PS 5.1 → rompe `ast.parse()` | `[System.IO.File]::WriteAllText` con `UTF8Encoding($false)` |
| `@'...'@` inline dentro de `.Replace()` | PowerShell se queda esperando cierre | Array de líneas + `-join` |
| `git commit -m "texto con * o $()"` | PowerShell interpreta globs y variables | `git commit -F archivo.txt` |
| `git log` sin `--no-pager` | Abre `less`, parece colgado | `git --no-pager log` |
| `python -c "..."` sin `PYTHONPATH` | `ModuleNotFoundError: agentic_os` | `$env:PYTHONPATH = "src"` |
| Crear ramas para todo | Overhead sin valor (1 humano + 1 agente) | Trabajar sobre master |
| Ejecutar `Set-Content` sin verificar | Puede dejar el fichero con BOM | Verificar los primeros bytes |

---

## 5. Tests

- **Suite completa:** `python -m pytest -q --maxfail=1`
- **Fichero concreto:** `python -m pytest tests/kernel/test_invariants.py -q`
- **Directorio:** `python -m pytest tests/kernel/ -q`

**Iteración rápida:** siempre `--maxfail=1` durante el trabajo. Solo al final
del ciclo correr la suite completa sin `maxfail`.

**Cuando un test falla:**

- El agente NO pide "todo el log" (es ruidoso).
- El agente pide **solo el bloque `FAILURES`** que pytest imprime arriba
  (~15 líneas con el traceback).
- Con eso se diagnostica el 95% de los casos.

**Si un bloque rompe un test preexistente:**

- No se "arregla el test" a la ligera. Primero se pregunta: ¿el test estaba
  bien y mi cambio rompió algo real? ¿O el test reflejaba un contrato antiguo?
- En el segundo caso, actualizar el test **documentando el por qué** en el
  mensaje del commit.

---

## 6. Formato de commits

Se usa **Conventional Commits** (sin tildes en el asunto):

```
tipo(scope): descripcion corta

Cuerpo opcional explicando QUE cambia y POR QUE.
Referencia a los AUD que cierra: Refs: docs/audits/KERNEL_INVARIANTS.md
```

Tipos usados: `fix`, `feat`, `docs`, `chore`, `refactor`, `test`.
Scopes usados: `kernel`, `policy`, `api`, `status`, `tests`.

**Los mensajes de commit van en un fichero temporal + `git commit -F`.**
Nunca `-m` inline si el texto lleva asteriscos, backticks, `$` o llaves.

---

## 7. Documentos de referencia

| Documento | Cuándo leerlo |
|---|---|
| `docs/STATUS.md` | Antes de empezar. Estado real del proyecto y deuda. |
| `docs/audits/KERNEL_INVARIANTS.md` | Los AUD-NN con severidad y evidencia. |
| `docs/spec/00_SYSTEM_PRINCIPLES.md` | La ley del sistema. |
| `docs/INVARIANTS.md` | Los invariantes del kernel (ejecutables). |
| `README.md` | Vista general del producto. |
| `docs/PRE_PRODUCTION_CHECKLIST.md` | Qué falta antes de producción real. |

**`docs/STATUS.md` se actualiza 1 vez por ciclo**, no en cada bloque. Eso
incluye la sección "Cobertura spec vs realidad" con porcentajes estimados.

---

## 8. Reglas de comunicación

### El agente

- Habla en español, directo, sin florituras.
- Admite errores propios sin rodeos ("es un bug mío").
- Cuando pide algo, es concreto ("pégame solo el bloque FAILURES").
- Cuando propone algo grande, primero explica y luego pide decisión.
- Nunca promete sin verificar (si dice "debería pasar", después confirma).
- Los números en tablas, no en párrafos.

### El humano

- Da feedback corto y directo. Si algo es pérdida de tiempo, lo dice.
- Prefiere iteración rápida sobre planificación exhaustiva.
- Cuando decide algo, lo deja claro y no vuelve atrás.
- Confía en el agente para detalles técnicos, pero revisa decisiones de diseño.

---

## 9. Ciclo de ejemplo (real, del 2026-09-18)

**Contexto:** se quiere cerrar el Ciclo A (endurecer kernel + endpoints spec).

1. Agente: "Bloque 1 — AUD-03 (validar tenant_id en `_load_policy`)".
   Script reemplaza una función por índice. Verifica con `Select-String`.
2. Humano: pega `OK: AUD-03 aplicado`.
3. Agente: "Bloque 2 — AUD-13 (risk classes)". Script con `Replace()` de
   bloques. Humano pega los `OK:`.
4. Agente: "Bloque 3 — AUD-16 (execute_action)". El `Contains()` falla
   (CRLF). El agente pide diagnóstico.
5. Humano: pega las líneas 420-447 de `executor.py`.
6. Agente: "Ahora veo el formato exacto. Reemplazo por índice." El fix
   funciona. Humano pega `OK: AUD-16 aplicado`.
7. Agente: "Bloque 4 — Suite completa". Humano pega `XXX passed`.
8. Agente: "Bloque 5 — Commit con `-F`". Humano pega el commit.
9. Agente: "Ciclo A cerrado. Actualizo STATUS.md."

**Duración:** ~30 minutos de interacción para 3 AUD + 2 endpoints + tests +
commit + actualización de docs.

---

## 10. Estado actual

### Commits recientes (orden cronológico)

| Hash | Asunto |
|---|---|
| `572b5ef` | `docs: anadir STATUS.md y sincronizar README` |
| `4478aa9` | `fix(kernel): AUD-01, AUD-02, AUD-11` (tests de capas + policy inyectable) |
| `26881e4` | `fix: AUD-04, AUD-19 + limpieza tests obsoletos` |
| `a8bde3a` | `fix(kernel): AUD-03, AUD-13, AUD-16` |
| `6066d79` | `feat(api): /api/approvals + /api/missions` |
| `bae89b8` | `fix(kernel): AUD-07, AUD-08, AUD-12, AUD-14` |

### AUD cerrados (13 de 22)

AUD-01, 02, 03, 04, 07, 08, 11, 12, 13, 14, 16, 19, 21.

### Pendientes (9 de 22)

- **AUD-05** — Camino tipado de eventos es código muerto.
- **AUD-09** — Ontología desconectada del runtime.
- **AUD-10** — `ENTITY_TYPE_REGISTRY` global de proceso.
- **AUD-15** — 3 representaciones de `Action`.
- **AUD-17** — resuelto (README) — verificar.
- **AUD-18** — resuelto (tests/bugs/ → tests/agent-notes/bugs/) — verificar.
- **AUD-20** — Deriva documental menor.
- **AUD-22** — Decisión: `data/policies/*.json` versionado o no.

### Gaps de auditorías internas

- Observability GAP 1: `correlation_id` se pierde en `Executor._audit()`.
- Permissions GAP 2: Scheduler no inyecta `TenantContext` en pipelines programados.
- Permissions GAP 3: doble path de decisión (`can()` vs `can_for_tenant()`).

### Suite actual

`540 passed, 1 warning in ~22s`. Comando: `python -m pytest -q --maxfail=1`.

---

## 11. Cuando llegue un agente nuevo

Checklist de onboarding:

1. **Lee este documento entero** (5 minutos).
2. **Lee `docs/STATUS.md`** (10 minutos).
3. **Corre `python -m pytest -q --maxfail=1`** para confirmar que el entorno
   está sano (30 segundos).
4. **Pregunta al humano** qué ciclo quiere atacar (A → B → C → D → E → F).
5. **Empieza por el primer bloque** del ciclo pendiente. No pidas plan completo;
   el humano prefiere iterar bloque a bloque.
6. **Cierra el ciclo con un commit único** y actualiza `docs/STATUS.md` si
   aplica.

Si algo no está claro: **pregunta antes de improvisar**. El humano valora la
precisión sobre la velocidad bruta, pero no quiere ceremonial.

---

**Última actualización:** 2026-09-18 tras el commit `bae89b8`.


---

# ANEXO: WORKING PROTOCOL FOR AI AGENTS

> Este anexo define como trabaja el usuario con un agente LLM. Sin
> leer esto, un agente puede saber que hacer (BUILD_PLAN) pero no
> como hacerlo. Es la mitad del trabajo de cada sesion.
>
> Aplica a cualquier agente que retome el repo: Cline, Claude,
> GPT, Gemini, lo que venga.
>
> Version 1. Creado 2026-09-18.

---

## A.1 Como se comunica el usuario

El usuario tiene un estilo muy concreto. Ignorarlo es la forma mas
rapida de perder su atencion.

**Hace**:

- Habla en espanol, directo, sin formalidades.
- Hace preguntas concretas: que falta, esto esta bien, como se firma.
- Se queja con razon cuando el agente divaga.
- Espera bloques PowerShell listos para copiar y pegar.
- Corrige si te has ido por las ramas. Escucha.
- Dice "sigue", "verde", "ok" cuando acepta.
- Dice "para", "espera", "dudas" cuando quiere clarificar.

**No hagas**:

- No des menus de opciones A/B/C si ya hay suficiente contexto.
- No reformules lo que acaba de decir.
- No te disculpes por cosas sin importancia.
- No expliques lo que vas a hacer antes de hacerlo. Hazlo.
- No metas emojis. No metas lenguaje corporativo.
- No des respuestas que podrias haber dado en 3 lineas en 30.
- No inventes. Si no sabes, miras el repo o preguntas.
- No uses "por supuesto", "claro", "entiendo perfectamente".
- No pidas confirmacion para cosas obvias.

**Cuando el usuario corrige**:

- Acepta sin justificarte.
- Aplica la correccion en el siguiente mensaje. Sin ensayo.
- Si la correccion implica rehacer algo, di "rehago bloque X" y lo
  rehaces.

---

## A.2 Flujo por bloque

Cada bloque de construccion sigue este ciclo estricto:

1. **Recon (read-only)**: pide al usuario que ejecute Select-String
   o Get-Content sobre los ficheros que vas a tocar. Nunca asumas
   el estado del repo sin verlo.

2. **Propuesta**: dices que vas a crear/modificar, en 3-5 lineas.
   Sin muro de texto.

3. **Bloque PowerShell**: das UN solo bloque para copiar y pegar.
   Si es muy largo, lo partes en 2-3 sub-bloques y dices "ejecuta
   el 1, pegamelo, luego el 2".

4. **Ejecucion del usuario**: el usuario lo ejecuta en su terminal.
   Te pega el output.

5. **Verificacion**: si el output es verde (tests passed, seccion
   presente, etc.), das el siguiente bloque. Si es rojo, pides mas
   informacion (bloque FAILURES) o corriges.

6. **Commit local**: al final del bloque, un bloque que hace
   git add + git commit + git push + git log.

7. **Actualizar BUILD_PLAN.md**: el bloque cerrado pasa de PENDING
   a DONE con los commits.

**Regla dura**: no se abre el siguiente bloque hasta que el actual
este cerrado (DONE + commits en origin/master). Si el usuario dice
"salto", se hace un sub-bloque.

**Regla dura 2**: no se hace commit por medio bloque. Solo cuando
tests verdes.

---

## A.3 Patrones PowerShell idempotentes

Los bloques PowerShell que das deben poder ejecutarse varias veces
sin romper nada. Si el usuario re-ejecuta por error, no pasa nada.

### A.3.1 Check de idempotencia

TODO bloque que crea o anade contenido debe empezar con un check:

```powershell
$src = [System.IO.File]::ReadAllText($path, [System.Text.Encoding]::UTF8)
if ($src -match "MARCADOR_UNICO_DEL_BLOQUE") {
    Write-Host "SKIP: ya existe"
} else {
    # escribir
}
```

Sin esto, un re-run duplica el contenido.

### A.3.2 Escribir ficheros (NUNCA here-strings)

MAL (se rompe al pegar en chat):

```powershell
$content = @'
linea 1
linea 2
'@
```

BIEN (array de strings):

```powershell
$lines = @(
    'linea 1',
    'linea 2',
    ''
)
[System.IO.File]::WriteAllLines($path, $lines, $utf8NoBom)
```

Donde `$utf8NoBom = New-Object System.Text.UTF8Encoding($false)`.

### A.3.3 Anadir contenido a un fichero existente

MAL (no acepta encoding):

```powershell
[System.IO.File]::AppendAllLines($path, $lines, $utf8NoBom)
```

BIEN:

```powershell
$src = [System.IO.File]::ReadAllText($path, [System.Text.Encoding]::UTF8)
$nuevo = $src.TrimEnd() + [Environment]::NewLine + [Environment]::NewLine + ($lines -join [Environment]::NewLine)
[System.IO.File]::WriteAllText($path, $nuevo, $utf8NoBom)
```

### A.3.4 Reemplazos en ficheros existentes

Para reemplazos pequenos, ok:

```powershell
$src = $src -replace 'texto viejo', 'texto nuevo'
[System.IO.File]::WriteAllText($path, $src, $utf8NoBom)
```

Para reemplazos de bloques grandes (mas de 10 lineas), mejor splice
por lineas:

```powershell
$lines = [System.IO.File]::ReadAllLines($path, [System.Text.Encoding]::UTF8)
$new = New-Object System.Collections.Generic.List[string]
for ($i = 0; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -match 'marcador de inicio') {
        # anadir bloque nuevo
        $new.Add('...')
        # saltar hasta marcador de fin
        while ($i -lt $lines.Count -and $lines[$i] -notmatch 'marcador de fin') { $i++ }
    }
    $new.Add($lines[$i])
}
[System.IO.File]::WriteAllLines($path, $new, $utf8NoBom)
```

### A.3.5 Encoding

SIEMPRE UTF-8 sin BOM:

```powershell
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
```

Al leer: `[System.Text.Encoding]::UTF8`.

### A.3.6 Path

Usar Join-Path o Resolve-Path:

```powershell
$path = Join-Path (Resolve-Path "docs").Path "BUILD_PLAN.md"
```

Nunca rutas absolutas hardcodeadas.

### A.3.7 Multiples bloques encadenados

Si un bloque es muy grande (>200 lineas de PowerShell), partirlo:

- Bloque A: crea estructura base.
- Bloque B: anade contenido.
- Bloque C: verifica + commit.

Cada uno comprobable antes del siguiente.

---

## A.4 Anti-patrones descubiertos

Errores que el usuario ya ha visto y no quiere repetir.

### A.4.1 No metas here-strings

El @'...'@ se rompe cuando el chat pega contenido con saltos raros.
Usa array de strings.

### A.4.2 No uses AppendAllLines con encoding

El metodo no tiene overload que acepte encoding. Da
MethodCountCouldNotFindBest. Usa ReadAllText + concat + WriteAllText.

### A.4.3 No commitees sin tests verdes

Regla dura. Aunque sea un cambio tonto.

### A.4.4 No reabras decisiones FIRMADAS

Si DXX esta FIRMADA en docs/DECISIONS.md, no la cambias. Si hay que
cambiarla, abres DXX+1 que supersede DXX con referencia.

### A.4.5 No toques kernel sin Kernel Boundary Rule

5 condiciones. PR separado. Tests kernel verdes antes y despues.
test_no_kernel_imports_domains verde.

### A.4.6 No digas "el orquestador decide"

El orquestador es Python. Ensambla. No decide. El LLM propone,
el sistema dispone. Si escribes "el orquestador elige el skill
correcto", estas violando el principio fundacional.

### A.4.7 No digas "el LLM ejecuta"

El LLM nunca ejecuta. Propone. Si dices "el LLM llama a la tool",
estas mal. La tool la llama Python, via Executor, via Policy.

### A.4.8 No mezcles capas

- kernel no importa dominio.
- connectors no importa cognition.
- domain no importa kernel internals.
- execution no importa orchestration.

Si dudas, mira los tests estructurales.

### A.4.9 No inventes proveedores LLM

Solo los que estan en docs/BUILD_PLAN.md apartado 5 (D22). Si
quieres anadir uno nuevo, propone DXX.

### A.4.10 No anadas dependencias sin justificar

Cada dependencia nueva es deuda futura. Avisa antes. Casi todo se
puede hacer con stdlib + pydantic + fastapi + httpx.

### A.4.11 No metas features no pedidas

Si el bloque es "feature flags", no anadas logging estructurado
porque queda bien. Cada bloque es lo que es. Features extra = otro
bloque.

---

## A.5 Vision polimorfica del sistema

Esto NO esta escrito en ningun spec. Es el contexto mental sin el
cual el trabajo de cada bloque no tiene sentido.

### A.5.1 En una frase

> Este repo no es un OS. Es la maquina que fabrica OSes. Software
> polimorfico: misma base, forma distinta segun el entorno.

### A.5.2 El principio

El kernel es axioma. El resto es lego.

El kernel no sabe que es un Lead, un Paciente o una Factura.
Solo sabe:

- Que es una Entidad valida.
- Que es una Accion valida.
- Que es una Policy que permite o niega.
- Que todo se audita en EventLog.

Eso no cambia nunca. Es como las leyes de la fisica: si pasa el
validador Pydantic, existe; si no, no existe.

### A.5.3 Los tenants son instancias de realidad

Cualquier cosa digital cabe como tenant porque toda cosa digital
humana se puede describir como:

```
Ontologia + Vocabulario + Pipelines + Policy
```

- Clonar HubSpot -> tenant.
- Clinica con triaje, agenda y facturacion -> tenant.
- Agencia que prospecta sola -> tenant.
- Sistema que no existe aun -> tenant.

Todas son lego de la biblioteca comunal de skills.

### A.5.4 El Tenant Compiler es el truco

No eres tu haciendo tenants a mano. Es un LLM dentro del sistema
(agentic-compiler) que lee:

> "Quiero una empresa de X que hace Y con Z"

Y produce:

- ontology.yaml del dominio.
- pipelines.py = combinaciones validas de skills comunales.
- policies/<tenant>.json especificas.
- enabled_capabilities.

El LLM no ejecuta nada del negocio. Solo es el arquitecto que
ensambla legos. Luego el sistema valida: existe esa combinacion de
skills? esa ontologia colisiona con DEFAULT_VOCAB? esa policy es
coherente? Si el compilador alucina, el kernel lo rechaza. Por eso
es seguro.

### A.5.5 Fundamento filosofico

Maturana - Autopoiesis y lenguajear: el lenguaje no es para
transmitir informacion, es coordinacion de coordinaciones de
acciones. Una empresa es eso: gente coordinando acciones mediante
distinciones linguisticas.

- Entity = una distincion ("esto es un Lead").
- Action = una coordinacion ("crear Lead").
- EventLog = la historia de coordinaciones que realmente pasaron.

Whitehead - Filosofia del proceso: el mundo no esta hecho de cosas,
sino de eventos. El ser es devenir.

- WorldState no existe como cosa. Es proyeccion derivada por
  replay(log).
- La verdad no es el estado, es el log de eventos inmutables.
- Por eso EventLog es frozen e inmutable.

Monismo + neurociencia: si todo es una sustancia y el cerebro es
predictivo, cognition/ modela:

- beliefs/ = creencias.
- observation.py = prediccion vs realidad.
- memory/{episodic,semantic,working}.py = taxonomia de memoria humana.
- reasoning/ = inferencia.

### A.5.6 Todas las empresas son iguales

A nivel de como se organizan y sus acciones, todas son iguales:

- Comunicacion (email, whatsapp).
- Investigacion (buscar info).
- CRM (acordarse de quien es quien).
- Ventas (persuadir).
- Contenido (explicar).
- Operaciones (hacer SOPs).

Cambian los sustantivos, no los verbos. Por eso la biblioteca
comunal de skills funciona: un communication.write_email sirve
igual a una clinica que a una agencia. Solo cambia el
tenant_overrides de tono y vocabulario.

### A.5.7 El modelo de negocio

No vendes software. Vendes empresa enlatada que ya factura.

Pitch: "Dame tu nicho y en 10 minutos te doy tu empresa automatica
viviendo en mi plataforma: prospecta, responde, agenda, cobra,
entrega y reporta. Tu solo apruebas y miras el dashboard."

Implicaciones tecnicas:

- infrastructure/tenancy/ no es multi-tenant clasico. Es
  multi-empresa.
- El compilador es la fabrica.
- Onboarding en 2 clicks o muerte.
- Aprobaciones como feature de venta (caja blanca).
- Pricing por misiones, no por seats.

### A.5.8 Lo que esto implica para cada bloque

- Bloque 1 (Skill): no lo hagas "con 10 skills". Hazlo con 3
  reales que sirvan a cualquier tenant.
- Bloque 0d (Tenant Compiler): no es un feature mas. Es el nucleo
  del polimorfismo. Cuando llegues, dimensiona bien.
- Bloque 10 (Frontend): el onboarding es requisito de producto, no
  UX. Es lo que convierte software en empresa enlatada.

---

## A.6 Manejo de fallos de tests

Cuando pytest falla, el flujo es:

1. NO commitear.
2. NO intentar arreglar a ciegas.
3. Pedir al usuario SOLO el bloque FAILURES, no todo el output.
4. Con eso, diagnosticar.
5. Corregir en un bloque nuevo.
6. Volver a correr tests.
7. Si verde, entonces commit.

### A.6.1 Que hacer si fallan 1-2 tests

- Pedir: python -m pytest <path> -q 2>&1 | Select-Object -First 40
- Leer el traceback exacto.
- Identificar si es:
  - Test mal escrito (lo mas comun cuando yo escribo el test).
  - Codigo mal escrito.
  - Contrato mal definido (spec vs codigo).
- Corregir en bloque aparte.

### A.6.2 Que hacer si fallan muchos tests

- Pedir: python -m pytest -q 2>&1 | Select-Object -Last 10
- Identificar si es un fallo comun (import roto, contrato roto).
- Si es comun, arreglar la causa raiz.
- Si son variados, atacar de uno en uno.

### A.6.3 Que hacer si un test se cuelga

- Pedir Ctrl+C.
- Revisar que el test no tenga while/sleep/infinite loops.
- Revisar timeouts en llamadas externas.

### A.6.4 Regla "no commitear en rojo"

Aunque el cambio sea minimo o obvio, no se commitea con tests
rojos. Si el usuario insiste, proponer:

- git stash del cambio.
- Investigar.
- Aplicar cuando este verde.

---

## A.7 Helper: bloque de fallo en rojo

Para que cada bloque de tests avise claro cuando falla, usar este
helper al inicio de la sesion:

```powershell
function Run-Pytest {
    param(
        [string]$Path = "tests/",
        [switch]$Last
    )
    if ($Last) {
        python -m pytest $Path -q 2>&1 | Select-Object -Last 5
    } else {
        python -m pytest $Path -q
    }
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "###############################################" -ForegroundColor Red
        Write-Host "#                                             #" -ForegroundColor Red
        Write-Host "#   TESTS FALLIDOS - NO COMMITEAR             #" -ForegroundColor Red
        Write-Host "#                                             #" -ForegroundColor Red
        Write-Host "#   Pega SOLO el bloque FAILURES al LLM       #" -ForegroundColor Red
        Write-Host "#   NO pegues todo el output                  #" -ForegroundColor Red
        Write-Host "#                                             #" -ForegroundColor Red
        Write-Host "###############################################" -ForegroundColor Red
        Write-Host ""
        return $false
    } else {
        Write-Host ""
        Write-Host "###############################################" -ForegroundColor Green
        Write-Host "#                                             #" -ForegroundColor Green
        Write-Host "#   TESTS VERDES - LISTO PARA COMMITEAR       #" -ForegroundColor Green
        Write-Host "#                                             #" -ForegroundColor Green
        Write-Host "###############################################" -ForegroundColor Green
        Write-Host ""
        return $true
    }
}
```

Uso:

```powershell
Run-Pytest "tests/kernel/"
Run-Pytest "tests/" -Last
```

Si el test pasa -> banner verde. Si falla -> banner rojo y devuelve
false.

Aviso al agente: siempre pedir el banner rojo al usuario cuando
algo falla, no toda la terminal.

---

## A.8 Checklist antes de commitear

Antes de dar el bloque de commit, verificar:

- [ ] Tests pasan (banner verde del helper o equivalente).
- [ ] Los ficheros correctos estan staged (git diff --cached --stat).
- [ ] El mensaje de commit sigue Conventional Commits (feat:,
      fix:, docs:, test:, refactor:, chore:).
- [ ] Si el bloque cierra una decision, el DECISIONS.md esta
      actualizado.
- [ ] Si el bloque cierra una skill nueva, SKILLS_LIBRARY.md esta
      actualizado.
- [ ] Si el bloque cierra un conector, CONNECTORS_STATUS.md esta
      actualizado.
- [ ] Si el bloque cierra parte de BUILD_PLAN, la entrada pasa a
      DONE con commits.

Si algo de esto falla, no commitear todavia.

---

## A.9 Como retomar una sesion nueva

Si eres un agente nuevo:

1. **Lee docs/AGENT_HANDOFF.md completo** (incluido este anexo).
2. **Lee docs/BUILD_PLAN.md**. Apartado 6, bloques.
3. **Lee docs/DECISIONS.md**. Mira cuales estan FIRMADAS.
4. **Lee docs/STATUS.md**. Estado real del repo.
5. **Ejecuta python -m pytest -q**. Confirma que los tests pasan
   antes de tocar nada.
6. **Pregunta al usuario por el bloque actual**. No asumas.
7. **Define el helper Run-Pytest** en tu primera sesion.
8. **Aplica este protocolo al pie de la letra**.

### A.9.1 Primer mensaje recomendado al usuario

> He leido AGENT_HANDOFF, BUILD_PLAN, DECISIONS y STATUS. El
> bloque actual es <X> (PENDING en BUILD_PLAN apartado 6). Antes
> de arrancar, necesito <recon de ficheros>. ¿Procedo con el recon?

### A.9.2 Cosas que NO preguntar

- No preguntes "¿por donde empezamos?". Esta escrito.
- No preguntes "¿que hago primero?". Esta escrito.
- No preguntes "¿quieres que use PowerShell o bash?". PowerShell.
- No preguntes "¿te parece bien el plan?". Ya esta firmado.
- No preguntes "¿confirmas que empiece?". Empieza con recon.

### A.9.3 Cosas que SI preguntar

- Estado actual del repo si hay dudas.
- Output de tests si algo falla.
- Preferencia entre 2 opciones concretas cuando el plan no lo cubre.
- Confirmacion de firma de una decision nueva.

---

## A.10 Glosario de terminos del usuario

- **Skill**: unidad atomica operativa comunal. No por tenant.
- **SkillStep**: paso de un skill, con mode (tool, llm, validate,
  branch, handoff).
- **SkillRunner**: ejecutor de skills. Python.
- **Agente**: manager de departamento. Perfil Python + rol LLM
  limitado.
- **Intent**: propuesta del LLM, validada por el sistema.
- **TaskPlan**: DAG de nodos, Python.
- **TaskScheduler**: ejecutor topologico. Python.
- **Mission**: instancia de ejecucion.
- **MissionTrace**: arbol reconstruible del EventLog.
- **SchemaAssembler**: convierte texto LLM en schema pydantic.
- **ModelRouter**: enruta a LLMs. Python.
- **Laia**: capa PR. Habla al usuario. NO ejecuta.
- **Orchestrator**: Python. Ensambla y dispone. No LLM.
- **Tenant Compiler**: fabrica pipelines de tenants nuevos.
- **Feature flag**: on/off por env var.
- **Kernel Boundary Rule**: 5 condiciones para tocar kernel.
- **Spec Contradiction Rule**: si spec contradice codigo, se para.
- **Lego**: skill reutilizable que combina con otras.
- **Polimorfismo**: misma base, forma distinta segun el tenant.
- **Empresa enlatada**: tenant listo para usar en 10 min.
- **Vertical slice**: prueba de aceptacion, no producto.

---

## A.11 Frases exactas del usuario que resumen su vision

Citadas para no perderlas:

> "es software polimorfico cuando termine las librerias tengo
> dentro un llm que construye tenants a partir de una prompt"

> "a mi repo le puedo enchufar cualquier sistema humano digital"

> "es software determinista hablable y auditable de caja blanca
> con ia agentica"

> "cualquier cosa digital me cabe como tenant"

> "es como una ia que te crea empresas automatizadas con
> inteligencia distribuida"

> "lo que se puede hacer en el mundo es lenguaje si tienes un
> kernel axiomatico que valida o rechaza, lo demas son piezas de
> lego"

> "y asi creo software de usar y tirar que se autoinstancia cuando
> se lo pides"

> "casi todas las empresas son practicamente iguales a nivel de
> como se organizan y de sus acciones"

> "mi plan es venderle a las personas del mundo su empresa
> automatica ya generando que vive en mi plataforma"

Estas frases son el norte. Cualquier decision tecnica debe ser
coherente con ellas.

---

## A.12 Mantenimiento del anexo

Este anexo se actualiza cuando:

- Se descubre un nuevo anti-patron del usuario.
- Se anade una regla de trabajo nueva.
- Se descubre un patron PowerShell mas robusto.
- El usuario expresa una vision nueva que no esta capturada.

Formato: anadir seccion A.XX al final. No reescribir el anexo
entero. Supersede por adicion, no por reemplazo.

---

## A.13 Cierre del anexo

Si has leido esto hasta el final, sabes como trabajar con este
usuario. Aplica el protocolo. No improvises. El plan ya esta
pensado. Tu trabajo es ejecutarlo con precision, en bloques
verificables, con tests verdes, y sin salirte del guion.

El usuario lleva el repo al 50%. Tu mision es llegar al 100%.
