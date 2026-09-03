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
        """Invoca un método MCP registrado con validación de contrato.

        - el servidor debe estar iniciado (fail-closed),
        - el método debe existir,
        - params debe ser un objeto (dict) o None,
        - el resultado debe ser estructurado (dict): un handler MCP nunca
          devuelve None silenciosamente.
        """
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

        if params is not None and not isinstance(params, dict):
            raise TypeError(
                f"MCP params debe ser un objeto (dict), recibido {type(params).__name__}"
            )

        result = handler(
            params or {}
        )

        if not isinstance(result, dict):
            raise TypeError(
                f"MCP method {name!r} debe devolver un dict, "
                f"recibido {type(result).__name__}"
            )

        return result
