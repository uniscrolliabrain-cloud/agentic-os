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
