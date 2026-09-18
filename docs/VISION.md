# VISION — Agentic OS

> Documento maestro del proyecto.
> Explica qué construimos, dónde está el repo hoy, y qué hacer.
> Fuente de verdad junto con `README.md`, `docs/spec/*` y `docs/audits/*`.

---

## 1. Qué estamos construyendo

### Software polimórfico

Agentic OS **no es una aplicación**. Es una **forma**.

Sistema operativo determinista, auditable y de caja blanca que ejecuta
software de terceros compilado dentro de él, sin tocar el kernel.

El kernel define invariantes universales. Cada empresa/proyecto aporta su
ontología, su policy, sus datos y su librería de operaciones. Todo eso
**debería** ser data, no código. Hoy es parcialmente así (§3).

### Kernel = leyes. Dominio = realidad.

Cita literal de `BaseDomain`:

> el kernel define qué **PUEDE** existir; el dominio define qué **EXISTE**.

El kernel **no debe saber** qué es un Patient, Lead, Invoice. Solo sabe qué
significa que exista una **entidad válida**.

### LLM propone. Sistema dispone.

El LLM nunca ejecuta directamente. Propone un `Intent`. La policy decide.
El `Executor` ejecuta. Todo queda en el `EventLog`.

### EventLog = memoria factual.

El mundo se **reconstruye por replay de eventos**, no se muta. El `WorldState`
es una proyección determinista del historial de hechos.

### Modelo mental del runtime
