# REF_BLOQUE_A — Especificaciones operativas (fuente: PLAN_IMPLEMENTACION_CLINE_V2 + AUDITORIA)

> Código ya implementado y verificado: A1-A4 en `src/agentic_os/kernel/ontology/domain_models.py` (18 tests).
> Este archivo solo contiene lo PENDIENTE (A5-A10) para no re-leer documentos grandes.
> NOTA: ontology_prompt_finalv3.md NO existe en el repo — usar solo las specs de abajo.

## A5 — ENTITY_TYPE_REGISTRY
- Registro `dict[str, type[BaseDomainModel]]` mapeando kind -> clase (9 entradas).
- Fail-closed: kind no registrado -> error claro (KeyError/ValueError), nunca silencioso.
- Integridad: cada clase del registro debe tener Literal kind que coincida con su clave.
- Test: 9 tipos registrados; entity_from_payload crea instancia correcta; kind desconocido falla; payload inválido lanza ValidationError.

## A6 — WorldState tipado (INV-5)
- `EntityUnion = Annotated[Union[Lead, Proposal, Brand, Campaign, BlogPost, CoachingClient, SessionNote, TherapyClient, Appointment], Field(discriminator="kind")]`
- `entities: Dict[str, EntityUnion]`
- Validator adicional: la clave del dict debe == entity.id (fail-closed).
- relations queda Dict[str, Dict[str, Any]] (se tipea con relations.py después).
- REESCRIBIR tests/bugs/test_bug8_pydantic_falso.py: ahora debe afirmar que payload inválido (age="gato") lanza ValidationError, entidad válida se guarda tipada, kind desconocido rechazado.
- Test nuevo: tests/kernel/test_worldstate_typed.py

## A7 — Applier transaccional
- apply() debe: (1) resolver tipo desde ENTITY_TYPE_REGISTRY, (2) validar evento contra ese tipo antes de aplicar, (3) si falla validación, devolver WorldState SIN modificar + error explícito (no parcial).
- Test: evento con payload inválido para su entity_type no altera el WorldState.

## A8 — Replay sin corrupción silenciosa
- replay() propaga fallo con el ÍNDICE del evento corrupto (excepción), no continúa.
- Test: log con evento corrupto en medio -> replay falla señalando cuál, no WorldState parcial.

## A9 — Migrar pipelines existentes a entidades tipadas
- pipeline_daily_social.py, pipeline_inbox_watcher.py, pipeline_leads_to_draft.py: donde manipulen Lead/Proposal/Campaign/BlogPost como dicts sueltos, usar clases tipadas de A2-A4.

## A10 — Gate del Bloque A
- pytest tests/kernel/ -q y tests/domains/ -q en verde, salida pegada.
- Script manual: crear Lead → evolucionar a Proposal → apply() → replay() desde cero → WorldState final coincide. Pegar script y salida.

## Bugs del doc de referencia a corregir SIEMPRE
1. get_current_user(): token = authorization.split(" ")[1] + guard len != 2 → 401
2. ExecutionTask.created_at: now_utc() (nunca utcnow)
3. No mezclar versiones duplicadas de clases

## Prohibido
pass como implementación, TODO como solución, Any para evitar tipar, except Exception: pass, debilitar tests existentes.