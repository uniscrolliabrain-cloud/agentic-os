# 094/100 - FASE 10.4 — AUDITORÍA "PYDANTIC DE VERDAD"
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
# TAREA 094/100 - FASE 10.4 — AUDITORÍA "PYDANTIC DE VERDAD"

## PROTOCOLO OBLIGATORIO ANTES DE CODIFICAR
1. Lee el estado REAL del repo: inspecciona src/, tests/, imports actuales.
2. No copies código de la especificación ciegamente. Si ya existe implementación superior, consérvala y adapta.
3. Localiza tests relacionados antes de tocar código.
4. No introduzcas pass, TODO, ..., Any, type: ignore, except: pass ni bypasses.

## CONTEXTO ARQUITECTÓNICO
Fase 10: HARDENING FINAL, TESTS Y PRODUCCIÓN
Invariante clave: LLM != Executor, Agent != Connector, Text != Command, Command != Permission. Todo efecto externo pasa por UserContext -> Policy -> Command -> Executor -> ConnectorRouter -> Connector.

## TU TAREA ESPECÍFICA
FASE 10.4 — AUDITORÍA "PYDANTIC DE VERDAD"

Busca globalmente:

dict[str, Any]
Dict[str, Any]
list[dict]
Dict[str, Dict[str, Any]]

Clasifica cada aparición.

No es necesario eliminar todo Any del sistema.

Pero:

- entidades;
- commands;
- contracts;
- outputs;
- execution plans;
- eventos críticos

deben estar tipados donde el contrato lo exige.

Sustituye únicamente las estructuras que representan datos contractuales.

No conviertas APIs dinámicas legítimas en modelos artificiales.

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
FASE 10.4 — AUDITORÍA "PYDANTIC DE VERDAD"

Busca globalmente:

dict[str, Any]
Dict[str, Any]
list[dict]
Dict[str, Dict[str, Any]]

Clasifica cada aparición.

No es necesario eliminar todo Any del sistema.

Pero:

- entidades;
- commands;
- contracts;
- outputs;
- execution plans;
- eventos críticos

deben estar tipados donde el contrato lo exige.

Sustituye únicamente las estructuras que representan datos contractuales.

No conviertas APIs dinámicas legítimas en modelos artificiales.
```

## CHECKLIST
- [ ] Inspeccione repo
- [ ] No copie ciego
- [ ] Tests verdes
- [ ] Entregue STATUS etc
