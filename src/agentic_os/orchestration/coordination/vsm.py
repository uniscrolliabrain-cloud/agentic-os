from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class VSM:

    """
    Stafford Beer Viable System Model.

    S1 Operation
    S2 Coordination
    S3 Control
    S4 Intelligence
    S5 Policy
    """

    state: Dict[str, Any]

    def __init__(self):

        self.state = {
            "S1": [],
            "S2": [],
            "S3": [],
            "S4": [],
            "S5": [],
        }

    def register(
        self,
        system: str,
        component: Any,
    ) -> None:

        if system not in self.state:
            raise ValueError(
                f"Sistema VSM desconocido: {system}"
            )

        self.state[system].append(
            component
        )

    def snapshot(self) -> Dict[str, Any]:

        return {
            key: list(value)
            for key, value
            in self.state.items()
        }
