"""Tests FASE 1.2 — contratos execution (Action/Command/Result) estrictos."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from agentic_os.contracts.execution import (
    Action,
    ActionParams,
    Command,
    ExecutionResult,
)


def test_action_params_rechaza_nombre_vacio() -> None:
    with pytest.raises(ValidationError):
        ActionParams(values={"": "<str>"})


def test_action_inmutable_y_forbid_extra() -> None:
    action = Action(
        capability="gmail_send",
        actor_id="actor-1",
        tenant_id="t-1",
    )
    with pytest.raises(ValidationError):
        action.capability = "otro"  # type: ignore[misc]
    with pytest.raises(ValidationError):
        Action(
            capability="gmail_send",
            actor_id="actor-1",
            tenant_id="t-1",
            campo_inventado="x",  # type: ignore[call-arg]
        )


def test_action_rechaza_capability_en_blanco() -> None:
    with pytest.raises(ValidationError):
        Action(capability="   ", actor_id="a", tenant_id="t")



def test_command_genera_correlation_id_por_defecto() -> None:
    command = Command(
        name="onboarding",
        tenant_id="t-1",
        actor_id="actor-1",
        actions=[
            Action(
                capability="crm_create",
                actor_id="actor-1",
                tenant_id="t-1",
            )
        ],
    )
    assert len(command.actions) == 1
    assert command.actions[0].tenant_id == "t-1"
    assert command.correlation_id
    assert isinstance(command.correlation_id, str)


def test_command_rechaza_acciones_de_otro_tenant() -> None:
    with pytest.raises(ValidationError):
        Command(
            name="onboarding",
            tenant_id="t-1",
            actor_id="actor-1",
            actions=[
                Action(
                    capability="crm_create",
                    actor_id="actor-1",
                    tenant_id="t-2",
                )
            ],
        )


def test_execution_result_no_filtra_valores() -> None:
    result = ExecutionResult(
        action_id="a-1",
        success=True,
        output_keys=["lead_id"],
    )
    assert result.output_keys == ["lead_id"]
    assert result.error is None
