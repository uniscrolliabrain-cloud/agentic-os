from __future__ import annotations
class CausalReasoner:
    def explain(self, event_id: str) -> dict:
        return {"event_id": event_id, "causes": []}
