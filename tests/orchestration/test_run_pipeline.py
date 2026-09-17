"""Test end-to-end del Intent(kind='run_pipeline').

Flujo: Intent -> _execute_intent -> _execute_pipeline_intent -> PipelineRunner.
Verifica que el despacho respeta policy, maneja pipelines desconocidos y
pasa los params al runner.
"""
from __future__ import annotations

from agentic_os.cognition.planning.intent import Intent
from agentic_os.interfaces.api import rest as rest_mod


# NOTA: NO reseteamos TenantRegistry._SHARED_INSTANCE. Hacerlo rompe otros
# tests (p.ej. test_hardening_fase4) que inyectan tenants en el singleton
# existente. El registry ya hace _maybe_reload() en cada get(), así que lee
# registry.json del disco automáticamente.


def test_run_pipeline_ejecuta_inbox_watcher():
    """Intent(run_pipeline, inbox_watcher) -> allow + pipeline ejecutado."""
    intent = Intent(
        kind="run_pipeline",
        payload={"pipeline_id": "inbox_watcher", "params": {}},
        goal="lanza inbox_watcher",
        rationale="test",
        confidence=1.0,
    )
    outcome = rest_mod._execute_intent(
        intent,
        tenant_id="bor-agencia",
        correlation_id="test-rp-1",
        command_id="cmd-rp-1",
    )
    assert outcome["action"] == "pipeline:inbox_watcher"
    assert outcome["policy_effect"] == "allow"
    assert outcome["result"] is not None
    # El runner devuelve status OK (o NO_LEADS_FILE si no hay leads)
    assert outcome["result"].get("status") in ("OK", "NO_LEADS_FILE")


def test_run_pipeline_desconocido_falla_limpio():
    """Un pipeline_id que no existe en el tenant -> note con 'desconocido'."""
    intent = Intent(
        kind="run_pipeline",
        payload={"pipeline_id": "no_existe", "params": {}},
        goal="x",
        rationale="y",
        confidence=1.0,
    )
    outcome = rest_mod._execute_intent(
        intent,
        tenant_id="bor-agencia",
        correlation_id="test-rp-2",
        command_id="cmd-rp-2",
    )
    assert outcome["action"] == "pipeline:no_existe"
    assert "desconocido" in (outcome.get("note") or "").lower()


def test_run_pipeline_sin_pipeline_id_denegado():
    """payload sin pipeline_id -> action=fail con note claro."""
    intent = Intent(
        kind="run_pipeline",
        payload={},
        goal="x",
        rationale="y",
        confidence=1.0,
    )
    outcome = rest_mod._execute_intent(
        intent,
        tenant_id="bor-agencia",
        correlation_id="test-rp-3",
        command_id="cmd-rp-3",
    )
    assert outcome["policy_effect"] == "deny"
    assert "pipeline_id" in (outcome.get("reason") or "").lower()


def test_run_pipeline_tenant_desconocido_denegado():
    """Tenant que no esta registrado -> deny fail-closed."""
    intent = Intent(
        kind="run_pipeline",
        payload={"pipeline_id": "inbox_watcher", "params": {}},
        goal="x",
        rationale="y",
        confidence=1.0,
    )
    outcome = rest_mod._execute_intent(
        intent,
        tenant_id="tenant-que-no-existe-xyz",
        correlation_id="test-rp-4",
        command_id="cmd-rp-4",
    )
    assert outcome["policy_effect"] == "deny"
