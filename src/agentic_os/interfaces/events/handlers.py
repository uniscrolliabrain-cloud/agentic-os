from __future__ import annotations

from typing import Callable, Dict, List


_handlers: Dict[
    str,
    List[Callable],
] = {}


def register(
    event_kind: str,
    handler: Callable,
) -> None:

    _handlers.setdefault(
        event_kind,
        [],
    ).append(handler)


def handlers_for(
    event_kind: str,
):

    return list(
        _handlers.get(
            event_kind,
            [],
        )
    )


def handle(event) -> None:

    for handler in handlers_for(
        event.kind
    ):
        handler(event)
