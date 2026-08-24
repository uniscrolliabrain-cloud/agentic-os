import pytest
from agentic_os.cognition.beliefs.belief import Belief
from agentic_os.cognition.planning.intent import Intent
from agentic_os.cognition.reasoning.proposer import LLMProposer, IntentProposalResponse, Proposer
from agentic_os.interfaces.llm.provider import MockLLMProvider


def test_deterministic_base_proposer():
    proposer = Proposer()
    intents = proposer.propose(beliefs=[], goal="Test goal")
    assert len(intents) == 1
    assert intents[0].goal == "Test goal"
    assert intents[0].rationale == "deterministic stub"


def test_llm_proposer_structured_proposal():
    mock_response = IntentProposalResponse(
        intents=[
            Intent(goal="Verify patient history", rationale="Needed before diagnosis"),
            Intent(goal="Check medication compatibility", rationale="Safety invariant"),
        ]
    )
    provider = MockLLMProvider(structured_response=mock_response)
    proposer = LLMProposer(provider=provider, domain_context="Clinic Domain")

    beliefs = [
        Belief(kind="allergy", content={"patient": "Patient123", "allergen": "Penicillin"}),
    ]
    intents = proposer.propose(beliefs=beliefs, goal="Treat patient with infection")

    assert len(intents) == 2
    assert intents[0].goal == "Verify patient history"
    assert intents[0].rationale == "Needed before diagnosis"
    assert intents[1].goal == "Check medication compatibility"
    assert "Clinic Domain" in (provider.last_prompt or "")
    assert "Patient123" in (provider.last_prompt or "")


def test_llm_proposer_filters_empty_goals():
    mock_response = IntentProposalResponse(
        intents=[
            Intent(goal="Valid goal", rationale="Valid rationale"),
            Intent(goal="", rationale="Empty goal should be filtered"),
        ]
    )
    provider = MockLLMProvider(structured_response=mock_response)
    proposer = LLMProposer(provider=provider)

    intents = proposer.propose(beliefs=[], goal="Test goal")
    assert len(intents) == 1
    assert intents[0].goal == "Valid goal"
