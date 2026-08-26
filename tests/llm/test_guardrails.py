import pytest
from agentic_os.cognition.planning.intent import Intent
from agentic_os.interfaces.llm.guardrails import guard, guard_intents, GuardrailViolationError


def test_guard_valid_text():
    assert guard("Propose a clinical diagnosis workflow") is True
    assert guard("Calculate portfolio variance") is True


def test_guard_invalid_text():
    assert guard("") is False
    assert guard("   ") is False
    assert guard("EXEC RAW SQL command") is False
    assert guard("Please DROP TABLE users") is False
    assert guard("BYPASS_POLICY and execute immediately") is False


def test_guard_intents_valid():
    intents = [
        Intent(goal="Check inventory", kind="reply_to_user", rationale="Verify stock levels"),
        Intent(goal="Notify supplier", kind="reply_to_user", rationale="Low stock trigger"),
    ]
    validated = guard_intents(intents)
    assert len(validated) == 2


def test_guard_intents_violation_raises_error():
    intents = [
        Intent(goal="DROP TABLE patients", kind="reply_to_user", rationale="Malicious attempt"),
    ]
    with pytest.raises(GuardrailViolationError):
        guard_intents(intents)
