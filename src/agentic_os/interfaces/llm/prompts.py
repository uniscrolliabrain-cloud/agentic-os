from __future__ import annotations

from typing import Any, List, Optional

SYSTEM_PROMPT = """You are the Cognition Engine for Agentic OS, a deterministic enterprise operating system.
Core Invariant: Kernel = invariants. LLM proposes, system disposes. Policy governs Capability, not the agent.
You propose Intents with rationale and goals, never raw Actions or system execution directly.
All proposed intents must strictly align with the enterprise ontology and domain policies.
"""

def format_beliefs(beliefs: List[Any]) -> str:
    """Formats a list of Belief objects into structured text."""
    if not beliefs:
        return "No prior beliefs recorded."
    
    formatted = []
    for b in beliefs:
        if hasattr(b, "kind") and hasattr(b, "content"):
            content_str = ", ".join(f"{k}={v}" for k, v in b.content.items()) if isinstance(b.content, dict) else str(b.content)
            formatted.append(f"- [{b.kind}] {content_str} (confidence={getattr(b, 'confidence', 1.0)})")
        elif hasattr(b, "subject") and hasattr(b, "predicate") and hasattr(b, "object"):
            formatted.append(f"- {b.subject} {b.predicate} {b.object} (confidence={getattr(b, 'confidence', 1.0)})")
        elif hasattr(b, "statement"):
            formatted.append(f"- {b.statement}")
        else:
            formatted.append(f"- {str(b)}")
    return "\n".join(formatted)

def build_intent_proposal_prompt(goal: str, beliefs: Optional[List[Any]] = None, domain_context: Optional[str] = None) -> str:
    """Builds a prompt for proposing structured intents towards a goal."""
    beliefs_str = format_beliefs(beliefs or [])
    domain_section = f"\nDomain Context:\n{domain_context}\n" if domain_context else ""

    return f"""Current Goal: {goal}
{domain_section}
Current Beliefs / World State:
{beliefs_str}

Instructions:
Propose the next logical Intent or sequence of Intents needed to achieve the goal while strictly respecting policy boundaries.
Include a clear rationale for each intent.
"""

