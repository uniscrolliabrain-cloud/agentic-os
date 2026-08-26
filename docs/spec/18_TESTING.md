# 18 — Testing

Criterio: **añadir un agente nuevo NO puede romper el núcleo** (`kernel/`) ni
otros agentes. Cada PR a un agente exige sus test.

## Capa de tests

1. **Unit** (pydantic contract): cada schema se instancia/valida contra casos válidos e inválidos.
2. **Microaction**: each tool devuelve lo que declara; validación rechaza lo malformado.
3. **Pipeline runner**: orden, validación inter-etapa, error_recovery, if_else.
4. **Policy**: deny-by-default, require_approval, tenant enable/disable.
5. **Orquestador**: router determinista y fallback LLM (con mock).
6. **Composición**: handoffs referencian ids existentes (integridad del catálogo).
7. **Regresión de núcleo**: los tests de `tests/kernel/` deben seguir pasando tras añadir un agente.

## Colocación

- Tests del núcleo: `tests/kernel/`.
- Tests por agente: `tests/agents/<agent_id>/`.

## Guardas obligatorias (pre-commit)

- Todos los `id` del catálogo únicos.
- Todo `handoff`/`dependencies` referencia un id existente.
- Toda `tool` declarada existe en `ToolRegistry`.
- Todo schema validable.
- `pytest` completo en verde.

## Contrato de aceptación para un miniagente nuevo

1. Especificación completa (plantilla `AGENT_SPECIFICATION_TEMPLATE.md`).
2. Schemas pydantic válidos.
3. Test unit + integración del pipeline.
4. No toca `kernel/`.
5. Corren `pytest tests/kernel/` sin fallos.
6. Actualiza el README/catálogo de referencia (docs/spec/*) si añade una familia/microacción.