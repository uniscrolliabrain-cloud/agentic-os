"""Contrato del loader `capability_catalog.py` (paso 4)."""
from __future__ import annotations

from typing import Any, Dict

import pytest

from agentic_os.connectors.core.capability_catalog import (
    ActionSpec,
    derive_action_spec,
    derive_catalog,
)
from agentic_os.connectors.core.models import RiskClass
from agentic_os.connectors.core.schemas import (
    DeleteParams,
    CalendarEventParams,
    CalendarListParams,
    FileReadParams,
    FileWriteParams,
    GenericParams,
    ListParams,
    ReadParams,
    SearchParams,
    SendParams,
)


def test_google_catalogo_derivado():
    g = derive_catalog("google")
    assert len(g) == 9
    assert set(g.keys()) == {
        "email.message.read", "email.message.send",
        "file.read", "file.create",
        "calendar.event.create", "calendar.event.read",
        "video.upload", "analytics.metrics.get", "analytics.search.query",
    }


def test_google_schemas_explicitos():
    g = derive_catalog("google")
    assert g["email.message.read"].params_schema is ListParams
    assert g["email.message.send"].params_schema is SendParams
    assert g["file.read"].params_schema is FileReadParams
    assert g["file.create"].params_schema is FileWriteParams
    assert g["calendar.event.create"].params_schema is CalendarEventParams
    assert g["calendar.event.read"].params_schema is CalendarListParams
    assert g["analytics.search.query"].params_schema is SearchParams


def test_google_requires_approval():
    g = derive_catalog("google")
    assert g["email.message.send"].requires_approval is True
    assert g["email.message.read"].requires_approval is False
    assert g["file.read"].requires_approval is False
    assert g["file.create"].requires_approval is False
    assert g["calendar.event.create"].requires_approval is False


def test_google_risk_classes():
    g = derive_catalog("google")
    assert g["email.message.send"].risk == RiskClass.EXTERNAL_COMMUNICATION
    assert g["email.message.read"].risk == RiskClass.READ_ONLY
    assert g["file.create"].risk == RiskClass.LOW_RISK_WRITE


def test_legacy_caps_deriva_con_arquetipos():
    specs: Dict[str, Dict[str, Any]] = {
        "fake": {
            "connector_id": "fake",
            "provider": "Fake",
            "caps": ["test.thing.read", "test.thing.send", "test.thing.delete"],
        }
    }
    c = derive_catalog(specs=specs)
    assert c["test.thing.read"].params_schema is ReadParams
    assert c["test.thing.send"].params_schema is SendParams
    assert c["test.thing.delete"].params_schema is DeleteParams
    assert c["test.thing.delete"].risk == RiskClass.DESTRUCTIVE
    assert c["test.thing.send"].risk == RiskClass.EXTERNAL_COMMUNICATION
    assert c["test.thing.send"].requires_approval is True
    assert c["test.thing.delete"].requires_approval is True


def test_schema_invalido_lanza_type_error():
    with pytest.raises(TypeError, match="no-Pydantic"):
        derive_action_spec("fake", "test.x.read", {"schema": "no-soy-una-clase"})


def test_action_spec_es_inmutable():
    g = derive_catalog("google")
    spec = g["email.message.send"]
    with pytest.raises(Exception):
        spec.kind = "otro"


def test_action_spec_rechaza_extra():
    with pytest.raises(Exception):
        ActionSpec(
            kind="x", providers=("y",),
            params_schema=SendParams, risk=RiskClass.READ_ONLY,
            campo_inventado="boom",
        )


def test_catalogo_completo_cubre_todos_los_providers():
    from agentic_os.connectors.providers import PROVIDER_SPECS
    full = derive_catalog()
    assert len(full) >= 200
    # ActionSpec.providers lista TODOS los providers que soportan cada kind.
    providers_in_catalog = {p for s in full.values() for p in s.providers}
    for provider_id in PROVIDER_SPECS:
        assert provider_id in providers_in_catalog, (
            f"provider '{provider_id}' no aparece en ningun ActionSpec"
        )


def test_email_send_presente_y_con_approval():
    full = derive_catalog()
    assert "email.message.send" in full
    assert full["email.message.send"].requires_approval is True