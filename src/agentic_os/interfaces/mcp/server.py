from __future__ import annotations

from typing import Callable, Dict


class MCPServer:

    def __init__(self):

        self._methods: Dict[
            str,
            Callable,
        ] = {}

        self.running = False

    def register(
        self,
        name: str,
        handler: Callable,
    ) -> None:

        if not name:
            raise ValueError(
                "MCP method name obligatorio"
            )

        self._methods[name] = handler

    def start(self) -> None:
        self.running = True

    def stop(self) -> None:
        self.running = False

    def call(
        self,
        name: str,
        params: dict | None = None,
    ):

        if not self.running:
            raise RuntimeError(
                "MCPServer no iniciado"
            )

        handler = self._methods.get(
            name
        )

        if handler is None:
            raise KeyError(
                f"MCP method no encontrada: {name}"
            )

        return handler(
            params or {}
        )
