"""Propuesta de Intents desde beliefs + goal.

Invariante: el LLM propone, el sistema dispone. Este modulo SOLO produce
Intents validados; nunca ejecuta acciones. Un Intent que no cumpla el
schema de su kind se descarta en silencio (fail-closed).

Fase A.2: el proposer conoce el catalogo de acciones (ACTION_CATALOG) y
valida cada intent contra su schema antes de devolverlo. Lo que no valida,
no llega al orchestrator.
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from ..beliefs.belief import Belief
from ..planning.intent import Intent
from ...connectors.core.capability_catalog import (
    catalog_prompt_block,
    get_action_spec,
    validate_action_params,
)
from ...interfaces.llm.provider import BaseLLMProvider, MockLLMProvider
from ...interfaces.llm.prompts import SYSTEM_PROMPT, build_intent_proposal_prompt
from ...interfaces.llm.guardrails import guard_intents


class IntentProposalResponse(BaseModel):
    """Structured container for LLM proposed intents."""
    intents: List[Intent] = Field(default_factory=list)


def _augment_prompt_with_catalog(base_prompt: str) -> str:
    """Anade el bloque del catalogo al prompt base. Determinista."""
    return (
        base_prompt
        + "\n\n"
        + catalog_prompt_block()
        + "\n\nPara cada intent, incluye SIEMPRE el campo 'payload' con los "
          "campos del kind elegido. Si te faltan datos, propone reply_to_user."
    )


def _validate_intent(intent: Intent) -> Optional[Intent]:
    """Devuelve el Intent con payload validado o None si no pasa el schema."""
    spec = get_action_spec(intent.kind)
    if spec is None:
        return None
    validated = validate_action_params(intent.kind, intent.payload)
    if validated is None:
        return None
    # Reemplaza payload por el modelo validado y vuelca a dict estricto.
    return intent.model_copy(update={"payload": validated.model_dump()})


class Proposer:
    """Deterministic base proposer stub."""

    def propose(
        self,
        beliefs: List[Belief],
        goal: str,
        domain_context: Optional[str] = None,
    ) -> List[Intent]:
        return [Intent(goal=goal, kind="reply_to_user", rationale="deterministic stub")]


class LLMProposer(Proposer):
    """LLM-backed proposer: propone Intents validados contra el catalogo.

    No ejecuta. Los Intents que no cumplen el schema de su kind se
    descartan (fail-closed). El payload que sobrevive esta tipado.
    """

    def __init__(
        self,
        provider: Optional[BaseLLMProvider] = None,
        domain_context: Optional[str] = None,
    ):
        self.provider = provider or MockLLMProvider(default_response='{"intents": []}')
        self.domain_context = domain_context

    def propose(
        self,
        beliefs: List[Belief],
        goal: str,
        domain_context: Optional[str] = None,
    ) -> List[Intent]:
        prompt = build_intent_proposal_prompt(
            goal=goal,
            beliefs=beliefs,
            domain_context=domain_context or self.domain_context,
        )
        prompt = _augment_prompt_with_catalog(prompt)

        proposal_response = self.provider.generate_structured(
            prompt=prompt,
            response_schema=IntentProposalResponse,
            system_instruction=SYSTEM_PROMPT,
        )

        # Fail-closed: se descartan los intents que no cumplen schema.
        candidates = list(proposal_response.intents)
        validated: List[Intent] = []
        for intent in candidates:
            v = _validate_intent(intent)
            if v is not None:
                validated.append(v)

        return guard_intents(validated)


__all__ = ["IntentProposalResponse", "Proposer", "LLMProposer"]