# Changelog

Todos los cambios notables de este proyecto se documentan en este archivo.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/),
y este proyecto usa [Semantic Versioning](https://semver.org/lang/es/).

## [Unreleased]

### Added
- CI (lint + type check + tests) vía GitHub Actions.
- Plantillas de Issue y Pull Request.
- `SECURITY.md`, `CONTRIBUTING.md`, `CHANGELOG.md`.
- Dependabot para dependencias pip, npm y GitHub Actions.

### Fixed
- Kernel: los dominios ya NO mutan `ENTITY_TYPE_REGISTRY` como side-effect en import (violaba los invariantes: registro inmutable tras `validate_registry_integrity()` y sin efectos en import). El registro es ahora explícito en bootstrap: `register_entity_types()` en `kernel/ontology/domain_models.py` + `AgenciaDomain.register_entities()` (compila la ontología fail-closed antes de registrar). Esto causaba 1 fallo global (`test_entity_registry::test_registry_contains_9_types`, 15 != 9 por contaminación entre tests).
- `orchestration/pipelines/runner.py`: el rewrite idempotente había perdido el dispatch a los pipelines registrados (`PIPELINES`), así como `_audit` y `emit_event`; el runner devolvía un stub sin `drafts_created`/`processed` (KeyError en 4 tests de pipelines). Restaurado el camino canónico Pipeline -> MicroAction -> Executor (Policy + auditoría) -> Tool -> EventLog, manteniendo la idempotencia por `command_id`.

### Removed
- `streamlit_app.py` (interfaz legacy): retirada en favor de `frontend/` (React), que ya cubre toda su funcionalidad (incluida la knowledge base por tenant) más gestión de tenants, schedules, skills, tools y artifacts.
- `prompt_cline`: prompt de trabajo interno obsoleto, sin relación con el código del repo.
- `tests/bugs/test_bug16_streamlit_threading_race.py`: probaba un bug exclusivo de la interfaz Streamlit ya eliminada.

## [0.1.0] - 2026-XX-XX

### Added
- Kernel determinista inicial (world, policy, ontology, types).
- Capa de cognición (beliefs, reasoning, planning, memory, skills, roles).
- Connector Kernel con 44 providers declarados (stub).
- API FastAPI + frontend React/Tailwind.
- Suite de tests con cobertura de bugs conocidos (`tests/bugs/`).
