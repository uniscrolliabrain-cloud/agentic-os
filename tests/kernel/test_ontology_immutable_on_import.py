"""Importar un dominio NO muta ENTITY_TYPE_REGISTRY."""
from __future__ import annotations

import importlib
import sys

from agentic_os.kernel.ontology.domain_models import ENTITY_TYPE_REGISTRY


def _fresh_import(module: str) -> None:
    for mod_name in list(sys.modules):
        if mod_name.startswith("agentic_os.domains"):
            del sys.modules[mod_name]
    importlib.import_module(module)


def test_import_agencia_does_not_mutate_registry():
    before = frozenset(ENTITY_TYPE_REGISTRY.keys())
    _fresh_import("agentic_os.domains.agencia")
    after = frozenset(ENTITY_TYPE_REGISTRY.keys())
    assert before == after, f"import muto el registry: {after - before}"


def test_import_compiler_does_not_mutate_registry():
    before = frozenset(ENTITY_TYPE_REGISTRY.keys())
    _fresh_import("agentic_os.domains.compiler")
    after = frozenset(ENTITY_TYPE_REGISTRY.keys())
    assert before == after, f"import muto el registry: {after - before}"


def test_explicit_registration_is_idempotent():
    from agentic_os.domains.agencia import AgenciaDomain
    AgenciaDomain.register_entities()
    size_1 = len(ENTITY_TYPE_REGISTRY)
    AgenciaDomain.register_entities()
    size_2 = len(ENTITY_TYPE_REGISTRY)
    assert size_1 == size_2