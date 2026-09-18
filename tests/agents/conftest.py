"""Fixture base: catalogo seedeado para tests de agentes."""
from __future__ import annotations

import pytest


@pytest.fixture()
def catalog():
    from agentic_os.cognition.agents.seed import build_catalog
    return build_catalog()

