import pytest
from agentic_os.cognition.beliefs.belief import Belief
from agentic_os.cognition.planning.intent import Intent
from agentic_os.cognition.reasoning.proposer import LLMProposer, IntentProposalResponse
from agentic_os.execution.action import Action
from agentic_os.interfaces.llm.provider import MockLLMProvider


def test_llm_proposer_strictly_returns_intents_never_actions():
    """Invariant 2: LLMProposer can ONLY propose Intent(goal), never Action or direct execution."""
    mock_payload = IntentProposalResponse(
        intents=[
            Intent(goal="Schedule clinical follow-up appointment", rationale="Monitor patient recovery"),
            Intent(goal="Send appointment confirmation email", rationale="Keep patient informed"),
        ]
    )
    provider = MockLLMProvider(structured_response=mock_payload)
    proposer = LLMProposer(provider=provider, domain_context="Clinic Domain")

    beliefs = [
        Belief(kind="patient_status", content={"patient": "P-100", "status": "recovering"}),
    ]

    proposed = proposer.propose(beliefs=beliefs, goal="Coordinate follow-up care")

    assert isinstance(proposed, list)
    assert len(proposed) == 2
    for item in proposed:
        assert isinstance(item, Intent)
        assert not isinstance(item, Action)
        assert hasattr(item, "goal")
        assert hasattr(item, "rationale")
        assert hasattr(item, "id")
        assert not hasattr(item, "capability")
        assert not hasattr(item, "run")
