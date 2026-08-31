"""FASE 2 de hardening: camino de ejecución unificado.

Criterio de aceptación: Executor.execute() con una capability que existe tanto
en ConnectorRouter como en el mock antiguo debe resolver por ConnectorRouter
(no por el registry viejo de mocks).
"""

from __future__ import annotations

import pytest

from src.agentic_os.execution.executor import Executor
from src.agentic_os.execution.tools import build_default_registry
from src.agentic_os.execution.tools.connector_bridge import (
    CANONICAL_ALIASES,
    ConnectorBridgeTool,
    build_capability_registry,
)


def _bare_executor() -> Executor:
    """Executor sin policy engine: aísla el camino de resolución de tools."""
    return Executor(registry=build_default_registry())


def test_gmail_send_resolves_via_connector_kernel():
    """gmail_send existe en el kernel (email.message.send) y en el mock:
    debe ganar el ConnectorRouter -> CONNECTOR_NOT_CONFIGURED (stub sin conectar)."""
    executor = _bare_executor()
    result = executor.execute(
        action="gmail_send",
        params={"to": "cliente@empresa.com", "subject": "hola", "body": "test"},
        context=None,
    )
    assert result["success"] is False
    assert "CONNECTOR_NOT_CONFIGURED" in result["error"]
    # El mock antiguo devolvería success con "status": "enviado": no debe ocurrir
    assert "status" not in str(result.get("output", {}))


def test_all_mock_actions_with_kernel_capability_use_bridge():
    """Toda acción mock cuya capability canónica existe en el kernel se registra
    como ConnectorBridgeTool (resolución unificada), no como mock."""
    registry = build_default_registry()
    kernel = build_capability_registry()
    for tool in registry.tools.values():
        canonical = CANONICAL_ALIASES.get(tool.name)
        if canonical and kernel.has_capability(canonical):
            assert isinstance(tool, ConnectorBridgeTool), (
                f"'{tool.name}' debería resolverse por el Connector Kernel "
                f"(capability canónica '{canonical}')"
            )


def test_bridge_capability_is_canonical():
    """El puente mapea a capabilities canónicas que el kernel conoce."""
    kernel = build_capability_registry()
    for action, canonical in CANONICAL_ALIASES.items():
        assert kernel.has_capability(canonical), (
            f"El alias '{action}' -> '{canonical}' apunta a una capability "
            "que el catálogo del kernel no declara"
        )


def test_unknown_action_still_fails_cleanly():
    executor = _bare_executor()
    result = executor.execute(action="accion_inexistente", params={}, context=None)
    assert result["success"] is False
    assert "no encontrada" in result["error"]


def test_dry_run_returns_preview_without_side_effect():
    """dry_run a través del puente: preview del kernel, nunca ejecución."""
    executor = _bare_executor()
    result = executor.execute(
        action="gmail_send",
        params={"to": "a@b.com", "subject": "s", "body": "b", "dry_run": True},
        context=None,
    )
    assert result["success"] is True
    output = result["output"]
    assert output.get("dry_run") is True
    # El preview viene normalizado dentro de output["output"] (contrato del bridge)
    assert "preview" in output.get("output", {})
    assert output.get("via") == "connector_kernel"