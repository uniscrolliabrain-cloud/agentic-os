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