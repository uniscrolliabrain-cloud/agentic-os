from __future__ import annotations

from typing import Any, Dict

from .base import Tool, ToolValidationError
from ...kernel.types.time import now_utc


class DocumentationCreateTool(Tool):
    """Tool determinista de Documentación: crea/actualiza un documento."""

    name = "documentation_create"

    def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        title = params.get("title", "")
        content = params.get("content", "")
        tags = params.get("tags", [])

        if not title:
            raise ToolValidationError("falta el campo title")

        return {
            "status": "creado",
            "title": title,
            "content_preview": content[:80],
            "tags": tags,
            "doc_id": f"doc-{abs(hash(title))}",
            "created_at": now_utc().isoformat(),
        }



class DocumentationSearchTool(Tool):
    """Tool determinista de Documentación: busca en la base de conocimiento."""

    name = "documentation_search"

    def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        query = params.get("query", "")
        max_results = int(params.get("max_results", 5))

        return {
            "status": "buscado",
            "query": query,
            "max_results": max_results,
            "results": [
                {"title": "Guía de onboarding", "snippet": "Pasos para dar de alta un cliente..."},
                {"title": "SOP: Gestión de incidencias", "snippet": "Procedimiento estándar..."},
            ],
        }