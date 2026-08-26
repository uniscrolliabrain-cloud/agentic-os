from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field

from ..beliefs.belief import Belief
from ..planning.intent import Intent
from ...interfaces.llm.provider import BaseLLMProvider, MockLLMProvider
from ...interfaces.llm.prompts import SYSTEM_PROMPT, build_intent_proposal_prompt
from ...interfaces.llm.guardrails import guard_intents


class IntentProposalResponse(BaseModel):
    """Structured container for LLM proposed intents."""
    intents: List[Intent] = Field(default_factory=list)


class Proposer:
    """Deterministic base proposer stub."""

    def propose(self, beliefs: List[Belief], goal: str) -> List[Intent]:
        return [Intent(goal=goal, kind="reply_to_user", rationale="deterministic stub")]


class LLMProposer(Proposer):
    """LLM-backed proposer: proposes Intents, never Actions directly."""

    def __init__(
        self,
        provider: Optional[BaseLLMProvider] = None,
        domain_context: Optional[str] = None,
    ):
        self.provider = provider or MockLLMProvider(default_response='{"intents": []}')
        self.domain_context = domain_context

    def propose(self, beliefs: List[Belief], goal: str) -> List[Intent]:
        prompt = build_intent_proposal_prompt(
            goal=goal,
            beliefs=beliefs,
            domain_context=self.domain_context,
        )

        proposal_response = self.provider.generate_structured(
            prompt=prompt,
            response_schema=IntentProposalResponse,
            system_instruction=SYSTEM_PROMPT,
        )

        return guard_intents(proposal_response.intents)

