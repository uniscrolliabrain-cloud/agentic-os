"""Aislamiento del ENTITY_TYPE_REGISTRY entre tests de dominio.

Motivo: `AgenciaDomain.register_entities()` muta el registro global del kernel
para añadir los kinds `agencia.*`. Si un test no restaura el registro, el
siguiente test de `test_entity_registry.py` ve 15 tipos en vez de 9 y falla
con `assert 15 == 9`.

Este fixture captura el estado ANTES de cada test y lo restaura DESPUÉS,
por lo que ningún test puede contaminar a otro, sin importar el orden.
"""
from __future__ import annotations

import pytest

from agentic_os.kernel.ontology.domain_models import ENTITY_TYPE_REGISTRY


@pytest.fixture(autouse=True)
def _isolate_entity_registry():
    snapshot = dict(ENTITY_TYPE_REGISTRY)
    yield
    ENTITY_TYPE_REGISTRY.clear()
    ENTITY_TYPE_REGISTRY.update(snapshot)
