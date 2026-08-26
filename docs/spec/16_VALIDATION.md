# 16 — Validación y QA

Cada microacción valida su **output contra su output_schema** antes de permitir
que el dato avance al siguiente paso o al resultado final.

## Validación de contrato (estructural)

1. `output_schema` es un JSON-schema; se valida con pydantic/model_validate.
2. Tipos, campos requeridos, formato de fechas/emails/URLs.
3. Fracaso → `ValidationFailed` → `FAILED` (no se propaga dato malformado).

## Validación semántica (reglas de calidad)

Cada microacción declara `validation` (reglas de negocio). Ejemplos:
- `email_valido`: destinatario con formato válido.
- `no_fabricar`: el contenido de un `Document` generado por LLM no introduce hechos sin fuente.
- `fuentes_suficientes`: mínimo 2 fuentes independientes en research.

## QA del pipeline

1. Nodo → `validate()` (schema) → `execute()` → `validate output` → `persist` → next.
2. Al final de la misión, un nodo **`qa` implícito** (si el agente lo declara) revisa criterios de calidad sobre el output final.
3. Reglas de QA se DB en `MiniAgentSchema.output_validation`.

## Regla transversal

"**Si no se puede validar, no se entrega.**" Un resultado dudoso pasa a `BLOCKED`/`NEEDS_APPROVAL`, nunca se publica como bueno.