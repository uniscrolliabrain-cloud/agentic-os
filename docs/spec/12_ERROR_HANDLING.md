# 12 — Manejo de errores

Define cómo se comporta el sistema cuando una microacción/pipeline/agente falla.

## Failure states (del catálogo)

Cada microacción declara su `error_states` (ej: `SearchUnavailable`, `SourceUnavailable`, `ExtractionFailed`, `SendFailed`, `ValidationFailed`, `InsufficientEvidence`).

## Retry policy

```python
retry_policy = {"max_retries": 1, "backoff": 1.5}
```
- Solo son **retryable** los errores transitorios (timeout, búsqueda/servicio no disponible, 429/5xx).
- Errores de validación o lógica NO son retryable (evitan loops infinitos).
- Último intento fallido → nodo `FAILED`.

## Timeout policy

- Cada microacción tiene `timeout_seconds` (default 60).
- Si se agota → se dispara el retry (si retryable) o `FAILED`.

## Estado del nodo

|Fallo|Tipo|Acción|
|---|---|---|
|Transitorio (red/servicio)|`BLOCK`|retry → RUNNING o FAILED|
|Validación output|`FAIL`|nodo FAILED, se registra causa en EventLog|
|Dependencia sin salida|`BLOCKED`|espera|
|Necesita humano|`NEEDS_APPROVAL`|se pausa (14)|

## Cadena de fallo

1. `microaction.error_states` captura el error tipado.
2. Se registra un **evento** en EventLog (`kind="MicroActionFailed"`).
3. Se aplica `error_recovery` del pipeline (si lo define) o se marca `FAILED`.
4. Los nodos dependientes → `BLOCKED`.
5. Se notifica al usuario (Laia / notify) con un resumen del fallo y opciones.

## Recuperación

- **Reintentar**: re-ejecuta el nodo fallido.
- **Saltar**: continúa con el siguiente nodo (si el pipeline lo permite).
- **Cancelar todo**: la misión pasa a `CANCELLED`.
De estas tres, la decisión SIEMPRE la toma un humano (o una regla de policy explícita del tenant), nunca el LLM.