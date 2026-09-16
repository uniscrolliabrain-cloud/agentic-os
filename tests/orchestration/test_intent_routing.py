from __future__ import annotations

from typing import List, Optional

from agentic_os.cognition.beliefs.belief import Belief
from agentic_os.cognition.planning.intent import Intent
from agentic_os.cognition.reasoning.proposer import Proposer
from agentic_os.interfaces.llm.provider import MockLLMProvider
from agentic_os.kernel.world.events import EventLog
from agentic_os.orchestration.orchestrator import DeterministicIntentRouter, Orchestrator


class SpyProposer(Proposer):
    def __init__(self) -> None:
        self.calls: List[tuple[List[Belief], str, Optional[str]]] = []

    def propose(
        self,
        beliefs: List[Belief],
        goal: str,
        domain_context: Optional[str] = None,
    ) -> List[Intent]:
        self.calls.append((beliefs, goal, domain_context))
        return [Intent(goal=goal, kind="reply_to_user", rationale="spy")]


def test_deterministic_router_precedes_llm_proposer() -> None:
    proposer = SpyProposer()
    orchestrator = Orchestrator(
        log=EventLog(),
        llm=MockLLMProvider(),
        proposer=proposer,
        router=DeterministicIntentRouter(),
    )

    intent = orchestrator.handle_user_message("Enviar un email ahora")

    assert intent.kind == "send_email"
    assert intent.rationale == "deterministic router"
    assert proposer.calls == []


def test_llm_proposer_receives_memory_context() -> None:
    proposer = SpyProposer()
    orchestrator = Orchestrator(
        log=EventLog(),
        llm=MockLLMProvider(),
        proposer=proposer,
        router=DeterministicIntentRouter(),
    )
    belief = Belief(kind="fact", key="tenant.name", content={"value": "Acme"})

    orchestrator.handle_user_message(
        "Prepara un resumen",
        beliefs=[belief],
        domain_context="tenant context",
    )

    assert len(proposer.calls) == 1
    assert proposer.calls[0][0] == [belief]
    assert proposer.calls[0][1] == "Prepara un resumen"
    assert "tenant context" in (proposer.calls[0][2] or "")
