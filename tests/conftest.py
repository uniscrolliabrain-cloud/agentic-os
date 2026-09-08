"""Configuración global de la suite.

Invariantes de test:
- Los tests NUNCA tocan APIs reales. Aunque .env traiga GOOGLE_REAL=true
  con credenciales válidas, la suite fuerza el camino stub/mock determinista.
  Un test que quiera ejercitar el camino real (p.ej. test_google_real_routing)
  debe activar settings.google_real de forma explícita en su propio fixture,
  que corre DESPUÉS de este autouse.
"""
from __future__ import annotations

import pytest

from agentic_os.infrastructure.config.settings import settings


@pytest.fixture(autouse=True)
def _no_real_google(monkeypatch):
    monkeypatch.setattr(settings, "google_real", False)
