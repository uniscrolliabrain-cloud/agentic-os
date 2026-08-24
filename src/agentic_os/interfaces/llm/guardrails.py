from __future__ import annotations

import re
from typing import List, Optional
from ...cognition.planning.intent import Intent


class GuardrailViolationError(Exception):
    """Raised when LLM output violates safety, deterministic invariants, or policy constraints."""
    pass


FORBIDDEN_EXEC_PATTERNS = [
    r"EXEC\s+RAW",
    r"DROP\s+TABLE",
    r"BYPASS_POLICY",
    r"SUDO\s+",
]


def guard(output: str) -> bool:
    """Validates raw LLM text against forbidden execution patterns."""
    if not output or not output.strip():
        return False

    for pattern in FORBIDDEN_EXEC_PATTERNS:
        if re.search(pattern, output, re.IGNORECASE):
            return False

    return True


def guard_intents(intents: List[Intent]) -> List[Intent]:
    """Validates a list of Intent proposals before submitting to the planning loop."""
    valid_intents: List[Intent] = []
    
    for intent in intents:
        if not intent.goal or not intent.goal.strip():
            continue
        
        # Ensure goal doesn't contain forbidden direct execution bypasses
        if not guard(intent.goal) or (intent.rationale and not guard(intent.rationale)):
            raise GuardrailViolationError(f"Intent violates guardrail policies: {intent.goal}")
        
        valid_intents.append(intent)
        
    return valid_intents

