from __future__ import annotations

from typing import List, Optional, Tuple

from pydantic import BaseModel, Field

from ..beliefs.belief import Belief
from ..memory.retrieval import retrieve_prompt_skills
from ..memory.store import MemoryItem, MemoryStore
from ..memory.working import WorkingMemory
from ..planning.intent import Intent
from ..skills.library import PROMPT_SKILLS
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
    """LLM-backed proposer: proposes Intents, never Actions directly.

    Divulgación progresiva de Prompt Skills: al recibir una petición se
    recuperan únicamente los top-3 Prompt Skills del tenant activo con mayor
    magnetismo (``MemoryStore.search`` determinista), se convierten en Beliefs
    ``kind="skill_available"`` con confianza proporcional al score, y se
    inyectan en la memoria de trabajo respetando ``WorkingMemory.capacity``
    (Ley de Miller) para no saturar el contexto del LLM.
    """

    def __init__(
        self,
        provider: Optional[BaseLLMProvider] = None,
        domain_context: Optional[str] = None,
        skill_store: Optional[MemoryStore] = None,
        tenant_id: str = "system",
    ):
        self.provider = provider or MockLLMProvider(default_response='{"intents": []}')
        self.domain_context = domain_context
        self.skill_store = skill_store if skill_store is not None else PROMPT_SKILLS
        self.tenant_id = tenant_id
        self.last_skill_beliefs: List[Belief] = []  # observable para tests/auditoría

    @staticmethod
    def _belief_from_skill(item: MemoryItem, score: int, max_score: int) -> Belief:
        confidence = (score / max_score) if max_score > 0 else 1.0
        return Belief(
            kind="skill_available",
            content={
                "skill_name": item.metadata.get("name", item.id),
                "version": item.metadata.get("version"),
                "pipeline_id": item.metadata.get("pipeline_id"),
                "instructions": item.content,
            },
            confidence=round(confidence, 4),
            source_observation_id="prompt_skill_top_k",
        )

    def _select_prompt_skills(self, goal: str, k: int = 3) -> List[Tuple[MemoryItem, int]]:
        return retrieve_prompt_skills(
            self.skill_store,
            query=goal,
            tenant_id=self.tenant_id,
            k=k,
        )

    def _build_working_memory(
        self,
        beliefs: List[Belief],
        prompt_skills: List[Tuple[MemoryItem, int]],
    ) -> Tuple[WorkingMemory, List[Belief]]:
        """Inyecta las skill beliefs y respeta ``capacity=7`` (Ley de Miller).

        Orden de prioridad en el cupo: Prompt Skills seleccionados (top-3)
        primero; el resto de creencias se recorta de forma determinista si el
        cupo se llena -> el contexto del LLM nunca se satura.
        """
        wm = WorkingMemory(
            beliefs=[b.model_dump() for b in beliefs],
            capacity=7,
        )
        max_score = max(
            (score for _, score in prompt_skills),
            default=1,
        ) or 1
        injected: List[Belief] = []
        for item, score in prompt_skills:
            if len(wm.beliefs) >= wm.capacity:
                break
            belief = self._belief_from_skill(item, score, max_score)
            wm.beliefs.append(belief.model_dump())
            injected.append(belief)
        return wm, injected

    def propose(self, beliefs: List[Belief], goal: str) -> List[Intent]:
        prompt_skills = self._select_prompt_skills(goal)
        wm, skill_beliefs = self._build_working_memory(beliefs, prompt_skills)
        self.last_skill_beliefs = skill_beliefs

        prompt = build_intent_proposal_prompt(
            goal=goal,
            beliefs=[Belief(**d) for d in wm.beliefs],
            domain_context=self.domain_context,
            skills=[item for item, _ in prompt_skills],
        )

        proposal_response = self.provider.generate_structured(
            prompt=prompt,
            response_schema=IntentProposalResponse,
            system_instruction=SYSTEM_PROMPT,
        )

        return guard_intents(proposal_response.intents)

