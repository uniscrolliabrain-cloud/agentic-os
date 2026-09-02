from __future__ import annotations

from threading import RLock
from typing import Callable, List


class EventBus:

    def __init__(self):

        self._handlers: List[
            Callable
        ] = []

        self._lock = RLock()

    def subscribe(
        self,
        handler: Callable,
    ) -> None:

        with self._lock:

            if handler not in self._handlers:
                self._handlers.append(
                    handler
                )

    def unsubscribe(
        self,
        handler: Callable,
    ) -> None:

        with self._lock:

            if handler in self._handlers:
                self._handlers.remove(
                    handler
                )

    def publish(
        self,
        event,
    ) -> None:

        with self._lock:
            handlers = list(
                self._handlers
            )

        for handler in handlers:
            handler(event)
