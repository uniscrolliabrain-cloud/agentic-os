"""Tests C1b/C1c/C1d: action types, Context, StateMachine."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from agentic_os.kernel.ontology.action_types import (
    ACTION_TYPES,
    FORBIDDEN_ACTION_ENTITY_PAIRS,
    is_forbidden_pair,
    is_valid_action,
)
from agentic_os.kernel.ontology.context import (
    CONTEXT_CATEGORIES,
    Context,
    ContextEntry,
)
from agentic_os.kernel.world.state_machine import (
    ALL_STATES,
    ALLOWED_TRANSITIONS,
    InvalidTransitionError,
    State,
    StateMachine,
)


# ---------------------------------------------- C1b: action_types

def test_16_verbos_exactos():
    assert len(ACTION_TYPES) == 16
    assert len(set(ACTION_TYPES)) == 16


def test_verbos_canonicos():
    assert "Discover" in ACTION_TYPES
    assert "Delete" in ACTION_TYPES
    assert "Monitor" in ACTION_TYPES


def test_is_valid_action():
    assert is_valid_action("Read") is True
    assert is_valid_action("Destroy") is False
    assert is_valid_action("") is False


def test_pares_prohibidos_9():
    assert len(FORBIDDEN_ACTION_ENTITY_PAIRS) == 9


def test_delete_person_prohibido():
    assert is_forbidden_pair("Delete", "Person") is True
    assert is_forbidden_pair("Delete", "core.person") is True


def test_publish_email_prohibido():
    assert is_forbidden_pair("Publish", "core.email") is True


def test_pares_no_listados_ok():
    assert is_forbidden_pair("Read", "core.person") is False
    assert is_forbidden_pair("Create", "core.email") is False


# ---------------------------------------------- C1c: Context

def test_8_categorias():
    assert len(CONTEXT_CATEGORIES) == 8
    assert set(CONTEXT_CATEGORIES) == {
        "User", "Client", "Project", "Brand", "Campaign", "Goal",
        "Constraint", "Permission",
    }


def test_context_entry_categoria_invalida():
    with pytest.raises(ValidationError):
        ContextEntry(tenant_id="t", category="Inventada")


def test_context_add_y_by_category():
    c = Context(tenant_id="t")
    c.add("User", {"name": "ana"})
    c.add("Brand", {"name": "acme"})
    c.add("User", {"name": "luis"})
    assert c.has("User") is True
    assert c.has("Client") is False
    assert len(c.by_category("User")) == 2


def test_context_entry_requiere_tenant():
    with pytest.raises(ValidationError):
        ContextEntry(category="User")


# ---------------------------------------------- C1d: StateMachine

def test_7_estados():
    assert len(ALL_STATES) == 7


def test_inicial_pending():
    assert StateMachine().current == State.PENDING


def test_transicion_valida():
    sm = StateMachine().transition(State.RUNNING)
    assert sm.current == State.RUNNING


def test_pending_a_completed_falla():
    with pytest.raises(InvalidTransitionError):
        StateMachine().transition(State.COMPLETED)


def test_pending_running_completed_pasa():
    sm = StateMachine().transition(State.RUNNING).transition(State.COMPLETED)
    assert sm.current == State.COMPLETED


def test_completed_es_terminal():
    sm = StateMachine(current=State.COMPLETED)
    assert sm.can_transition(State.RUNNING) is False
    with pytest.raises(InvalidTransitionError):
        sm.transition(State.RUNNING)


def test_cancelled_es_terminal():
    sm = StateMachine(current=State.CANCELLED)
    assert sm.can_transition(State.RUNNING) is False


def test_needs_approval_puede_volver_a_running():
    sm = StateMachine(current=State.NEEDS_APPROVAL)
    assert sm.can_transition(State.RUNNING) is True
    assert sm.can_transition(State.CANCELLED) is True


def test_blocked_vuelve_a_running():
    sm = StateMachine(current=State.BLOCKED)
    assert sm.can_transition(State.RUNNING) is True


def test_failed_permite_retry():
    sm = StateMachine(current=State.FAILED)
    assert sm.can_transition(State.RUNNING) is True
    assert sm.can_transition(State.PENDING) is True


def test_transicion_a_estado_invalido():
    with pytest.raises(InvalidTransitionError):
        StateMachine().transition("VOLANDO")


def test_estado_actual_invalido_al_construir():
    with pytest.raises(ValidationError):
        StateMachine(current="VOLANDO")


def test_machine_es_inmutable():
    sm = StateMachine()
    with pytest.raises(ValidationError):
        sm.current = State.RUNNING


def test_todas_las_transiciones_declaradas():
    for state, allowed in ALLOWED_TRANSITIONS.items():
        for target in allowed:
            assert target in ALL_STATES, (state, target)

