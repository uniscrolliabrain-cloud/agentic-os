"""Tests del Compilador Ontológico (FASE 2).

Valida que el YAML de dominio genera capabilities tipadas, que cada canonical
resuelve en el Connector Kernel, y que el dry-run devuelve preview sin efecto.
"""

import asyncio
import sys
from pathlib import Path

import pytest
import yaml

PROJ = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJ / "src"))

from agentic_os.connectors import CapabilityRegistry, ConnectorFactory, ConnectorRouter
from agentic_os.connectors.core.models import Command, HealthStatus
from agentic_os.connectors.providers import PROVIDER_SPECS, register_builtin_providers
from agentic_os.kernel.ontology.capabilities import Capability

YAML_PATH = PROJ / "src" / "agentic_os" / "domains" / "marketing_ficticio" / "ontology.yaml"


@pytest.fixture()
def domain() -> dict:
    return yaml.safe_load(YAML_PATH.read_text(encoding="utf-8"))


@pytest.fixture()
def registry() -> CapabilityRegistry:
    reg = CapabilityRegistry()
    factory = ConnectorFactory()
    register_builtin_providers(factory)
    for provider in PROVIDER_SPECS:
        reg.register(factory.create(provider))
    return reg


def test_domain_yaml_valido(domain):
    assert domain["domain"] == "marketing_ficticio"
    assert len(domain["vocabulary"]["entities"]) == 3  # lead, cita, campana
    assert len(domain["vocabulary"]["capabilities"]) == 6


def test_capabilities_pydantic(domain):
    raw = domain["vocabulary"]["capabilities"]
    for item in raw:
        cap = Capability(
            name=item["name"],
            description=f"{item['action']} {item['entity']} -> {item['canonical']}",
            requires_tools=item.get("tools", []),
        )
        assert cap.name.startswith("crm.")
        assert cap.requires_tools, f"{cap.name} debe declarar tools"


def test_canonical_resuelve_en_registry(domain, registry):
    for item in domain["vocabulary"]["capabilities"]:
        canonical = item["canonical"]
        assert registry.has_capability(canonical), f"{canonical} no resuelve"


def test_dry_run_devuelve_preview(registry):
    """Un Command dry-run sobre una capability del dominio devuelve preview, nunca ejecuta."""
    router = ConnectorRouter(registry)
    cmd = Command(
        capability="crm.deal.create",
        params={"name": "EmpresaX"},
        dry_run=True,
        execution_id="test-dry",
    )
    res = asyncio.run(router.route(cmd))
    assert res.dry_run is True
    assert res.preview is not None
    assert res.preview["capability"] == "crm.deal.create"
    assert res.preview["connector"] == "hubspot"
    # El connector es un stub sin conectar: nunca toca el mundo real
    assert "never" in res.preview["note"] or "dry-run" in res.preview["note"]