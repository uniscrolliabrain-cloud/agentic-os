"""Contrato de errores de tools: documentation_create (bugfix FASE 3.3).

Una tool NUNCA devuelve {"error": ...}: lanza ToolValidationError y el
Executor lo traduce a success=False (ToolFailed). Antes documentation_create
devolvía {"error": "falta el campo title"} envuelto en success=True.
"""
from __future__ import annotations

import pytest

from agentic_os.execution.tools.base import ToolValidationError
from agentic_os.execution.tools.documentation_tool import (
    DocumentationCreateTool,
    DocumentationSearchTool,
)


def test_create_sin_title_lanza_error() -> None:
    with pytest.raises(ToolValidationError):
        DocumentationCreateTool().run({"title": ""})


def test_create_valido_devuelve_resultado_simulado() -> None:
    result = DocumentationCreateTool().run(
        {"title": "Guía", "content": "contenido largo...", "tags": ["ops"]}
    )
    assert result["status"] == "creado"
    assert result["title"] == "Guía"
    assert result["doc_id"].startswith("doc-")


def test_search_devuelve_resultados() -> None:
    result = DocumentationSearchTool().run({"query": "onboarding"})
    assert result["status"] == "buscado"
    assert isinstance(result["results"], list) and result["results"]
