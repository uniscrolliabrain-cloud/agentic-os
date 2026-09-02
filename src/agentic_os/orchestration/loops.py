from __future__ import annotations

from typing import Any, Callable, Optional


class Loop:

    def __init__(
        self,
        step: Optional[
            Callable[[Any], Any]
        ] = None,
        max_iterations: int = 10,
    ):

        self.step = step
        self.max_iterations = max(
            1,
            max_iterations,
        )

    def run(
        self,
        state: Any = None,
    ) -> Any:

        if self.step is None:
            return state

        current = state

        for _ in range(
            self.max_iterations
        ):

            result = self.step(
                current
            )

            if result is None:
                break

            if (
                isinstance(result, dict)
                and result.get(
                    "done"
                )
            ):
                return result.get(
                    "state",
                    result,
                )

            current = result

        return current
