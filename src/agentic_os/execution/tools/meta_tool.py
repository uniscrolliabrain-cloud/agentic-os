from __future__ import annotations

import os
import uuid
from typing import Any, Dict

from .base import Tool, ToolValidationError


def _meta_real_api_ready() -> bool:
    """FASE 6: preparado para la fase real — cuando existan las credenciales
    en el entorno, la tool las usará en vez de simular. Nunca se exponen."""
    return bool(os.environ.get("META_PAGE_ID") and os.environ.get("META_PAGE_ACCESS_TOKEN"))


class MetaPostPublishTool(Tool):
    """Publica un post en Meta (Facebook/Instagram). SIMULADO por ahora.

    NO llama a graph.facebook.com todavía. Cuando se active la fase real,
    leerá META_PAGE_ID y META_PAGE_ACCESS_TOKEN del entorno (.env por tenant).
    """

    name = "meta_post_publish"

    def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        page_id = params.get("page_id", "")
        message = params.get("message", "")
        image_url = params.get("image_url", "")

        missing = [
            field
            for field, value in (("page_id", page_id), ("message", message), ("image_url", image_url))
            if not value
        ]
        if missing:
            raise ToolValidationError(f"faltan campos obligatorios: {', '.join(missing)}")

        return {
            "status": "SIMULATED",
            "id": f"sim_{uuid.uuid4().hex[:12]}",
            "real_execution": False,
            "payload": {"page_id": page_id, "message": message, "image_url": image_url},
            "real_api_ready": _meta_real_api_ready(),
        }


class MetaCarouselPublishTool(Tool):
    """Publica un carrusel en Meta. SIMULADO por ahora (sin API real)."""

    name = "meta_carousel_publish"

    def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        page_id = params.get("page_id", "")
        message = params.get("message", "")
        image_url = params.get("image_url", "")

        missing = [
            field
            for field, value in (("page_id", page_id), ("message", message), ("image_url", image_url))
            if not value
        ]
        if missing:
            raise ToolValidationError(f"faltan campos obligatorios: {', '.join(missing)}")

        return {
            "status": "SIMULATED",
            "id": f"sim_{uuid.uuid4().hex[:12]}",
            "real_execution": False,
            "payload": {"page_id": page_id, "message": message, "image_url": image_url},
            "real_api_ready": _meta_real_api_ready(),
        }
