"""Bug 19 - TenantRegistry singleton no multi-worker: _SHARED_INSTANCE no comparte entre workers uvicorn"""

import pytest
import tempfile
from pathlib import Path

from agentic_os.infrastructure.tenancy.registry import TenantRegistry


def test_singleton_same_instance_within_process():
    """Dentro del mismo proceso, el singleton debe devolver la misma instancia."""
    TenantRegistry._SHARED_INSTANCE = None
    r1 = TenantRegistry()
    r2 = TenantRegistry()
    assert r1 is r2, "Singleton no devuelve la misma instancia dentro del proceso"


def test_registry_persists_to_disk():
    """El registry debe persistir en disco para que otros workers puedan leerlo."""
    with tempfile.TemporaryDirectory() as tmpdir:
        registry_path = Path(tmpdir) / "registry.json"
        TenantRegistry._SHARED_INSTANCE = None
        registry = TenantRegistry(registry_path=registry_path)

        # Crear un tenant
        from agentic_os.infrastructure.tenancy.models import TenantConfig
        t = registry.create("Test Corp", "testcorp", config={"domain": "generic"})
        assert t is not None

        # El archivo debe existir
        assert registry_path.exists(), "Registry no persiste a disco"


def test_registry_reloads_from_disk():
    """Una nueva instancia debe poder cargar los datos del disco."""
    with tempfile.TemporaryDirectory() as tmpdir:
        registry_path = Path(tmpdir) / "registry.json"

        # Crear registry y añadir tenant
        TenantRegistry._SHARED_INSTANCE = None
        r1 = TenantRegistry(registry_path=registry_path)
        r1.create("ACME Corp", "acme", config={"domain": "generic"})

        # Reset singleton (simular otro worker)
        TenantRegistry._SHARED_INSTANCE = None
        r2 = TenantRegistry(registry_path=registry_path)

        # Debe cargar el tenant del disco
        tenants = r2.list_all()
        assert len(tenants) >= 1, "Registry no recarga datos del disco (multi-worker)"
