# Contribuir a Agentic OS

Gracias por contribuir. Este proyecto tiene un kernel determinista con invariantes
estrictas — lee `docs/INVARIANTS.md` y `docs/spec/00_SYSTEM_PRINCIPLES.md` antes
de tocar `kernel/`, `policy/` o `connectors/`.

## Setup local

```bash
git clone <repo>
cd uniscrolliabrain-cloud-agentic-os
pip install -e ".[dev]"
cp .env.example .env   # rellena tus keys de desarrollo
pytest                 # confirma que todo pasa antes de empezar
```

## Flujo de trabajo

1. Crea una rama desde `main`: `feature/<descripcion>`, `fix/<descripcion>` o `hotfix/<descripcion>`.
2. Haz commits atómicos siguiendo [Conventional Commits](https://www.conventionalcommits.org/):
   `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`.
3. Si corriges un bug, añade un test de regresión en `tests/bugs/test_bugNN_<descripcion>.py`,
   siguiendo el patrón ya existente en el repo.
4. Antes de abrir el PR:
   ```bash
   ruff check .
   mypy src/agentic_os
   pytest
   ```
5. Abre el PR contra `main` usando la plantilla. La CI debe pasar en verde.
6. Si el cambio toca `kernel/`, `policy/` o `connectors/`, se requiere revisión
   explícita (ver `.github/CODEOWNERS`).

## Reglas de arquitectura (resumen)

- El LLM **propone**, nunca ejecuta directamente.
- Toda acción pasa por `PolicyEngine` antes del `Executor`.
- `EventLog` es la fuente de verdad; `WorldState` es derivado.
- La ontología separa metamodelo (invariante) de vocabulario (extensible por dominio).

Para más detalle, ver `docs/ARCHITECTURE.md` y `docs/spec/`.

## Reportar bugs o proponer features

Usa las plantillas de Issues (`🐛 Bug report` / `✨ Feature request`).
