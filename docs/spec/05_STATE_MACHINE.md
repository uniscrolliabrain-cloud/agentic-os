# 05 — Máquina de estados

Estado = en qué momento del ciclo de vida está una entidad, misión o tarea.
El estado es un tipo del metamodelo (ver `01_ONTOLOGY.md`).

## Estados

```
PENDING → RUNNING → COMPLETED
              │        │
              ├→ FAILED
              ├→ BLOCKED
              └→ NEEDS_APPROVAL → RUNNING / CANCELLED
```

| Estado | Significado | Transiciones válidas |
|---|---|---|
| PENDING | En cola, aún no empieza | RUNNING, CANCELLED |
| RUNNING | Está ejecutándose | COMPLETED, FAILED, BLOCKED, NEEDS_APPROVAL |
| COMPLETED | Terminó con éxito | (terminal) |
| FAILED | Terminó con error irrecuperable | RETRY → PENDING/RUNNING |
| BLOCKED | Espera un recurso/dato externo | RUNNING |
| NEEDS_APPROVAL | Espera decisión humana | RUNNING, CANCELLED |
| CANCELLED | Abandonado por decisión | (terminal) |

## Reglas

1. Toda transición de estado se registra como **evento** en el EventLog
   (`kernel/world/events.py`). Sin evento no hay cambio de estado.
2. La máquina es **determinista**: no se permiten transiciones no listadas.
3. La clase `StateMachine` se implementa en `kernel/world/state.py` y se valida
   con pydantic en `05` del código.

## Persistencia

El estado "derivado" de un agregado se obtiene por **replay** del EventLog
(`kernel/world/replay.py`). Nunca se muta directamente: se aplica el evento y
se proyecta. Esto mantiene la invariante *"WorldState derivable, Event immutable"*.