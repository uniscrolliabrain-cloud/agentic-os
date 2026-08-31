from __future__ import annotations

from typing import Any, Dict

from .base import Tool, ToolValidationError


class WebScrapeTool(Tool):
    """Tool determinista de Web Scraping: extrae contenido de una URL.

    En producción se conecta a un motor real de scraping con las políticas
    de robots.txt y rate-limiting del tenant. Aquí simulamos con mock.
    """

    name = "web_scrape"

    def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        url = params.get("url", "")

        if not url:
            raise ToolValidationError("falta el campo url")

        return {
            "status": "scrapeado",
            "url": url,
            "title": "Ejemplo de página",
            "content_preview": "Contenido extraído de la página...",
            "links_count": 12,
            "scraped_at": "2026-08-25T12:00:00",
        }


class WebSearchTool(Tool):
    """Tool determinista de Búsqueda Web: busca información."""

    name = "web_search"

    def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        query = params.get("query", "")
        max_results = int(params.get("max_results", 5))

        if not query:
            raise ToolValidationError("falta el campo query")

        return {
            "status": "buscado",
            "query": query,
            "max_results": max_results,
            "results": [
                {"title": "Resultado 1", "url": "https://example.com/1", "snippet": "Lorem ipsum..."},
                {"title": "Resultado 2", "url": "https://example.com/2", "snippet": "Dolor sit amet..."},
            ],
        }