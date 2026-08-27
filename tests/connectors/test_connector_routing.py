"""Routing determinista, riesgo y garantías de no-filtración de secretos."""

import asyncio
import os

import pytest

from agentic_os.connectors import CapabilityRegistry, ConnectorFactory, ConnectorRouter
from agentic_os.connectors.core.models import Command, risk_class_for
from agentic_os.connectors.providers import register_builtin_providers


@pytest.fixture()
def router() -> ConnectorRouter:
    f = ConnectorFactory()
    register_builtin_providers(f)
    reg = CapabilityRegistry()
    for cid in ("hubspot", "openai", "google", "smtp_imap"):
        reg.register(f.create(cid))
    return ConnectorRouter(reg)


def _cmd(capability: str, params: dict | None = None, dry_run: bool = False) -> Command:
    return Command(
        capability=capability,
        params=params or {},
        workspace_id="ws_test",
        execution_id="exec_test_1",
        dry_run=dry_run,
    )


def test_stub_devuelve_not_configured(router):
    res = asyncio.run(router.route(_cmd("crm.contact.create", {"name": "A"})))
    assert res.ok is False
    assert res.error_type == "CONNECTOR_NOT_CONFIGURED"
    assert res.capability == "crm.contact.create"


def test_capability_desconocida_da_unsupported(router):
    res = asyncio.run(router.route(_cmd("familia.inexistente.accion")))
    assert res.ok is False
    assert res.error_type == "UNSUPPORTED_OPERATION"


def test_dry_run_devuelve_preview_sin_efecto(router):
    res = asyncio.run(router.route(_cmd("email.message.send", {"to": "a@b.c"}, dry_run=True)))
    assert res.dry_run is True
    assert res.preview is not None
    assert res.preview["capability"] == "email.message.send"
    assert res.preview["note"].startswith("dry-run")


def test_risk_class_classification():
    assert risk_class_for("email.message.send") == "EXTERNAL_COMMUNICATION"
    assert risk_class_for("finance.refund.create") == "FINANCIAL"
    assert risk_class_for("database.record.delete") == "DESTRUCTIVE"
    assert risk_class_for("crm.contact.read") == "READ_ONLY"
    assert risk_class_for("otra.accion.desconocida") == "LOW_RISK_WRITE"


def test_resultado_nunca_contiene_secretos(router, monkeypatch):
    monkeypatch.setenv("HUBSPOT_ACCESS_TOKEN", "secreto-123-no-filtrar")
    res = asyncio.run(router.route(_cmd("crm.contact.create")))
    assert "secreto-123-no-filtrar" not in res.model_dump_json()


def test_command_es_inmutable():
    cmd = _cmd("crm.contact.create")
    with pytest.raises(Exception):
        cmd.capability = "hackejada"
