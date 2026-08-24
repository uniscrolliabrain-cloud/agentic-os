from __future__ import annotations
from typing import Callable, Any, Dict
from .state import WorldState
Projection = Callable[[WorldState], Dict[str, Any]]
def project_by_kind(state: WorldState, kind: str) -> Dict[str, Any]:
    return {eid: data for eid, data in state.entities.items() if data.get("kind")==kind}
