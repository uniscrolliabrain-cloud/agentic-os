"""
Demo: Using Gemini LLM with Agentic OS Cognition & Reasoning

Requires:
    export GEMINI_API_KEY="your_api_key_here"  (or set in .env)
"""

import os
from agentic_os.cognition.beliefs.belief import Belief
from agentic_os.cognition.reasoning.proposer import LLMProposer
from agentic_os.interfaces.llm.provider import GeminiProvider, MockLLMProvider
from agentic_os.infrastructure.config.settings import Settings


def main():
    settings = Settings()
    api_key = os.getenv("GEMINI_API_KEY") or settings.gemini_api_key

    if api_key:
        print(f"[*] Initializing GeminiProvider with model: {settings.gemini_model}...")
        provider = GeminiProvider(api_key=api_key)
    else:
        print("[!] No GEMINI_API_KEY found. Falling back to MockLLMProvider for offline demo...")
        provider = MockLLMProvider(
            default_response='''{
                "intents": [
                    {"goal": "Check medication interactions", "rationale": "Patient is on antibiotics"},
                    {"goal": "Schedule follow-up consultation", "rationale": "Monitor treatment efficacy"}
                ]
            }'''
        )

    proposer = LLMProposer(
        provider=provider,
        domain_context="Clinic Healthcare Domain - High Safety Constraints",
    )

    beliefs = [
        Belief(kind="diagnosis", content={"patient": "Patient_402", "condition": "Bacterial Infection"}),
        Belief(kind="allergy", content={"patient": "Patient_402", "allergen": "Amoxicillin"}),
    ]

    goal = "Establish safe treatment plan for patient"
    print(f"\n[*] Proposing Intents for Goal: '{goal}'...")
    intents = proposer.propose(beliefs=beliefs, goal=goal)

    print(f"\n[+] Generated {len(intents)} Validated Intents (Invariants verified):")
    for i, intent in enumerate(intents, 1):
        print(f"  {i}. Intent ID: {intent.id}")
        print(f"     Goal:      {intent.goal}")
        print(f"     Rationale: {intent.rationale}\n")


if __name__ == "__main__":
    main()
