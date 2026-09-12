"""Configuración global de la suite.

Invariantes de test:
- Los tests NUNCA tocan APIs reales. Aunque .env traiga GOOGLE_REAL=true
  con credenciales válidas, la suite fuerza el camino stub/mock determinista.
  Un test que quiera ejercitar el camino real (p.ej. test_google_real_routing)
  debe activar settings.google_real de forma explícita en su propio fixture,
  que corre DESPUÉS de este autouse.
"""
from __future__ import annotations

import os

import pytest

os.environ.setdefault(
    "CREDENTIAL_ENCRYPTION_KEY",
    "test-secret-key-32-chars-long-abc!!",
)

from agentic_os.infrastructure.config.settings import settings


@pytest.fixture(autouse=True)
def _no_real_google(monkeypatch):
    monkeypatch.setattr(settings, "google_real", False)


@pytest.fixture(autouse=True)
def _test_encryption_key(monkeypatch):
    import agentic_os.connectors.auth.credential_store as cs_mod

    monkeypatch.setattr(settings, "credential_encryption_key", "test-secret-key-32-chars-long-abc!!")
    monkeypatch.setenv("CREDENTIAL_ENCRYPTION_KEY", "test-secret-key-32-chars-long-abc!!")
    cs_mod._module_fernet = None
