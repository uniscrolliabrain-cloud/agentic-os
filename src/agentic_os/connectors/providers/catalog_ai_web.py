"""Catálogo de providers de IA, búsqueda web, navegador y extracción.

Cada entrada declara: capabilities canónicas, tipo de auth y variables de
entorno para cargar credenciales cuando se CONECTE. Ninguno se conecta aquí:
el connector nace como stub (connected=False).
"""

from typing import Any, Dict

PROVIDER_SPECS_AI_WEB: Dict[str, Dict[str, Any]] = {
    "tavily": {
        "connector_id": "tavily", "provider": "Tavily", "auth_type": "bearer",
        "caps": ["web.search", "web.news.search"],
        "token_env": "TAVILY_API_KEY",
        "base_url": "https://api.tavily.com",
    },
    "serpapi": {
        "connector_id": "serpapi", "provider": "SerpAPI", "auth_type": "api_key",
        "caps": ["web.search"],
        "token_env": "SERPAPI_API_KEY",
        "base_url": "https://serpapi.com",
    },
    "exa": {
        "connector_id": "exa", "provider": "Exa", "auth_type": "bearer",
        "caps": ["web.search"],
        "token_env": "EXA_API_KEY",
        "base_url": "https://api.exa.ai",
    },
    "brave_search": {
        "connector_id": "brave_search", "provider": "Brave Search", "auth_type": "bearer",
        "caps": ["web.search", "web.image.search", "web.local.search"],
        "token_env": "BRAVE_SEARCH_API_KEY",
        "base_url": "https://api.search.brave.com/res/v1",
    },
    "firecrawl": {
        "connector_id": "firecrawl", "provider": "Firecrawl", "auth_type": "bearer",
        "caps": ["web.page.fetch", "web.page.extract", "web.site.crawl", "web.site.map"],
        "token_env": "FIRECRAWL_API_KEY",
        "base_url": "https://api.firecrawl.dev",
    },
    "jina_reader": {
        "connector_id": "jina_reader", "provider": "Jina Reader", "auth_type": "bearer",
        "caps": ["web.page.extract"],
        "token_env": "JINA_API_KEY",
        "base_url": "https://r.jina.ai",
    },
    "browser": {
        "connector_id": "browser", "provider": "Playwright", "auth_type": "none",
        "caps": ["browser.session.create", "browser.navigate", "browser.click",
                 "browser.fill", "browser.select", "browser.scroll",
                 "browser.screenshot", "browser.download", "browser.extract", "browser.close"],
        "token_env": None,
        "note": "Ejecuta en local/remote runner; sesiones aisladas por workspace.",
    },
}