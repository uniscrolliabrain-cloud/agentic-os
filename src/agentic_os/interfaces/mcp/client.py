from __future__ import annotations

from typing import Any, Optional


class MCPClient:

    def __init__(
        self,
        transport: Any = None,
    ):
        self.transport = transport
        self.connected = False

    def connect(self) -> None:

        if self.transport is None:
            raise RuntimeError(
                "MCP transport no configurado"
            )

        if hasattr(
            self.transport,
            "connect",
        ):
            self.transport.connect()

        self.connected = True

    def disconnect(self) -> None:

        if (
            self.transport is not None
            and hasattr(
                self.transport,
                "disconnect",
            )
        ):
            self.transport.disconnect()

        self.connected = False

    def call(
        self,
        method: str,
        params: Optional[dict] = None,
    ):

        if not self.connected:
            raise RuntimeError(
                "MCPClient no conectado"
            )

        if not hasattr(
            self.transport,
            "call",
        ):
            raise RuntimeError(
                "MCP transport no soporta call()"
            )

        return self.transport.call(
            method,
            params or {},
        )
