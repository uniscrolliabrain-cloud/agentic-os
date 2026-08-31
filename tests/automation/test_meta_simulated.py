"""FASE 6: tools de Meta simulan publicaciones (nunca llaman a graph.facebook.com)."""

from __future__ import annotations

import pytest

from agentic_os.execution.tools.base import ToolValidationError
from agentic_os.execution.tools.meta_tool import (
    MetaCarouselPublishTool,
    MetaPostPublishTool,
)


def test_meta_post_publish_simulado() -> None:
    tool = MetaPostPublishTool()
    out = tool.run({
        "page_id": "1234",
        "message": "Hola mundo",
        "image_url": "https://img.example.com/1.jpg",
    })
    assert out["status"] == "SIMULATED"
    assert out["real_execution"] is False
    assert out["id"].startswith("sim_")
    assert out["payload"]["page_id"] == "1234"


def test_meta_post_publish_valida_campos() -> None:
    tool = MetaPostPublishTool()
    with pytest.raises(ToolValidationError):
        tool.run({"page_id": "1234"})  # falta message e image_url


def test_meta_carousel_publish_simulado() -> None:
    tool = MetaCarouselPublishTool()
    out = tool.run({
        "page_id": "5678",
        "message": "Carrusel",
        "image_url": "https://img.example.com/2.jpg",
    })
    assert out["status"] == "SIMULATED"
    assert out["real_execution"] is False
    assert out["id"].startswith("sim_")


def test_meta_registradas_en_registry() -> None:
    from agentic_os.execution.tools import build_default_registry

    reg = build_default_registry()
    assert reg.get("meta_post_publish") is not None
    assert reg.get("meta_carousel_publish") is not None
    assert reg.get("drive_list_files") is not None
    assert reg.get("drive_read_file") is not None
    assert reg.get("gmail_create_draft") is not None
    assert reg.get("gmail_list_unread") is not None