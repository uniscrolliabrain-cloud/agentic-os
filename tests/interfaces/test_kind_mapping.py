"""Tests del mapping determinista Intent.kind → action (#15 del hardening).

La heurística por substrings ("email" in kind, "slack" in kind...) fue
eliminada: solo kinds canónicos en ACTION_BY_KIND se ejecutan.
"""
from __future__ import annotations

from agentic_os.interfaces.api.rest import ACTION_BY_KIND, _map_kind_to_action


def test_mapping_canonico_exacto() -> None:
    assert _map_kind_to_action("send_email") == "gmail_send"
    assert _map_kind_to_action("create_appointment") == "calendar_create_event"
    assert _map_kind_to_action("create_event") == "calendar_create_event"
    assert _map_kind_to_action("web_scrape") == "web_scrape"


def test_mapping_normaliza_espacios_y_caso() -> None:
    assert _map_kind_to_action("Send_Email") == "gmail_send"
    assert _map_kind_to_action("  send_email  ") == "gmail_send"


def test_kind_desconocido_fail_closed() -> None:
    # El LLM puede proponer kinds libres; el Kernel NO infiere acciones:
    # kind sin entrada canónica → None → no se ejecuta nada.
    assert _map_kind_to_action("kind_fantasma") is None
    assert _map_kind_to_action(None) is None
    assert _map_kind_to_action("") is None


def test_heuristica_substring_eliminada() -> None:
    # Estos kinds antes macheaban por substring ("email" in k) y disparaban
    # tools: ahora deben ser ignorados (fail-closed, determinista).
    assert _map_kind_to_action("miemail_custom") is None
    assert _map_kind_to_action("notifslack") is None
    assert _map_kind_to_action("urls_de_interes") is None


def test_todas_las_actions_del_mapping_existen_en_executor() -> None:
    from agentic_os.execution.tools import build_default_registry

    registry = build_default_registry()
    for action in ACTION_BY_KIND.values():
        assert action in registry.tools, (
            f"ACTION_BY_KIND apunta a '{action}' que no existe en ToolRegistry"
        )
