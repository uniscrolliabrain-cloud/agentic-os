"""Aislamiento del ENTITY_TYPE_REGISTRY entre tests de dominio.

El root `tests/conftest.py` ya instala el mismo autouse fixture; este archivo
se mantiene por compatibilidad con tests que lo importan explicitamente.
"""