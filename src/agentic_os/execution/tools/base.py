from __future__ import annotations
from abc import ABC, abstractmethod


class ToolValidationError(Exception):
    """FASE 3.3: contrato único de error de tools.

    Una tool NUNCA devuelve {"error": ...}: si los parámetros son inválidos
    o la ejecución falla de forma controlada, lanza ToolValidationError. El
    Executor la captura y la traduce a success=False (evita el bug de
    reportar éxito con un error dentro del output, p. ej. GmailSendTool
    devolviendo {"error": ...} envuelto en success=True).
    """


class Tool(ABC):
    name: str
    @abstractmethod
    def run(self, params: dict) -> dict: ...
