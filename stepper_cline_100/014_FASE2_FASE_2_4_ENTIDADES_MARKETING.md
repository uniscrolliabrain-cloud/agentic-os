# 014/100 - FASE 2.4 — ENTIDADES MARKETING
FASE 2 - ONTOLOGÍA TIPADA Y WORLDSTATE
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
# TAREA 014/100 - FASE 2.4 — ENTIDADES MARKETING

## PROTOCOLO OBLIGATORIO ANTES DE CODIFICAR
1. Lee el estado REAL del repo: inspecciona src/, tests/, imports actuales.
2. No copies código de la especificación ciegamente. Si ya existe implementación superior, consérvala y adapta.
3. Localiza tests relacionados antes de tocar código.
4. No introduzcas pass, TODO, ..., Any, type: ignore, except: pass ni bypasses.

## CONTEXTO ARQUITECTÓNICO
Fase 2: ONTOLOGÍA TIPADA Y WORLDSTATE
Invariante clave: LLM != Executor, Agent != Connector, Text != Command, Command != Permission. Todo efecto externo pasa por UserContext -> Policy -> Command -> Executor -> ConnectorRouter -> Connector.

## TU TAREA ESPECÍFICA
FASE 2.4 — ENTIDADES MARKETING

Implementa/consolida:

marketing.brand
marketing.campaign

Brand debe validar domain_url y las restricciones de tone_of_voice.

Campaign debe validar:

- brand_id;
- name;
- objective;
- channels;
- budget_limit;
- status.

Los campos deben estar cerrados mediante Pydantic.

No utilices dict[str, Any] como sustituto del modelo físico.

Añade tests para valores inválidos de:

- URL;
- tone_of_voice;
- channels;
- budget;
- status;
- strings fuera de límites.

Ejecuta pytest.

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
FASE 2.4 — ENTIDADES MARKETING

Implementa/consolida:

marketing.brand
marketing.campaign

Brand debe validar domain_url y las restricciones de tone_of_voice.

Campaign debe validar:

- brand_id;
- name;
- objective;
- channels;
- budget_limit;
- status.

Los campos deben estar cerrados mediante Pydantic.

No utilices dict[str, Any] como sustituto del modelo físico.

Añade tests para valores inválidos de:

- URL;
- tone_of_voice;
- channels;
- budget;
- status;
- strings fuera de límites.

Ejecuta pytest.
```

## CHECKLIST
- [ ] Inspeccione repo
- [ ] No copie ciego
- [ ] Tests verdes
- [ ] Entregue STATUS etc
