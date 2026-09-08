# 091/100 - FASE 10.1 — PYPROJECT
FASE 10 - HARDENING FINAL, TESTS Y PRODUCCIÓN
Estado: - [ ] PENDIENTE

PROTOCOLO CLINE:
1. Inspecciona repo real antes de tocar codigo
2. No copies codigo de spec ciegamente
3. NUNCA pass/TODO/.../Any/type:ignore/except:pass/bypass
4. UserContext->Policy->Command->Executor->ConnectorRouter->Connector
5. LLM!=Executor
6. Todo cambio con tests + STATUS/ARCHIVOS/CAMBIOS/TESTS/RESULTADO/INVARIANTES/RIESGOS


## PROMPT PARA CLINE
```text
# TAREA 091/100 - FASE 10.1 — PYPROJECT

## PROTOCOLO OBLIGATORIO ANTES DE CODIFICAR
1. Lee el estado REAL del repo: inspecciona src/, tests/, imports actuales.
2. No copies código de la especificación ciegamente. Si ya existe implementación superior, consérvala y adapta.
3. Localiza tests relacionados antes de tocar código.
4. No introduzcas pass, TODO, ..., Any, type: ignore, except: pass ni bypasses.

## CONTEXTO ARQUITECTÓNICO
Fase 10: HARDENING FINAL, TESTS Y PRODUCCIÓN
Invariante clave: LLM != Executor, Agent != Connector, Text != Command, Command != Permission. Todo efecto externo pasa por UserContext -> Policy -> Command -> Executor -> ConnectorRouter -> Connector.

## TU TAREA ESPECÍFICA
FASE 10.1 — PYPROJECT

Audita pyproject.toml contra imports reales.

Comprueba dependencias de:

- pydantic;
- pydantic-settings;
- fastapi;
- uvicorn;
- cryptography;
- python-jose;
- bcrypt;
- httpx;
- apscheduler;
- google-genai;
- google-api-python-client si se usa;
- groq si se usa.

No añadas paquetes simplemente porque aparecen en la especificación.

Añade solo dependencias realmente utilizadas.

Separa runtime y dev dependencies.

Ejecuta instalación limpia en entorno virtual.

## ENTREGABLES OBLIGATORIOS AL FINALIZAR
Debes responder con:
STATUS: PASS/FAIL
ARCHIVOS MODIFICADOS: lista
CAMBIOS: bullet points
TESTS: qué tests ejecutaste y resultado
RESULTADO: resumen técnico
INVARIANTES PROTEGIDAS: cuáles
RIESGOS: si quedan

## COMANDOS A EJECUTAR
pytest tests/ -k <relevante> -q
ruff check src tests
mypy src --ignore-missing-imports (si aplica)

No avances al siguiente prompt hasta validar este.

```

## SPEC ORIGINAL
```text
FASE 10.1 — PYPROJECT

Audita pyproject.toml contra imports reales.

Comprueba dependencias de:

- pydantic;
- pydantic-settings;
- fastapi;
- uvicorn;
- cryptography;
- python-jose;
- bcrypt;
- httpx;
- apscheduler;
- google-genai;
- google-api-python-client si se usa;
- groq si se usa.

No añadas paquetes simplemente porque aparecen en la especificación.

Añade solo dependencias realmente utilizadas.

Separa runtime y dev dependencies.

Ejecuta instalación limpia en entorno virtual.
```

## CHECKLIST
- [ ] Inspeccione repo
- [ ] No copie ciego
- [ ] Tests verdes
- [ ] Entregue STATUS etc
