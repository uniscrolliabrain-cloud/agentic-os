"""Bug 14 - Back-office inyectando en chat: rest.py mete "⚙ (back office)" rompiendo voz de Laia"""

import pytest


def test_backoffice_does_not_inject_into_conversation():
    """El orquestador NO debe inyectar mensajes en la conversación del usuario."""
    import inspect
    from agentic_os.interfaces.api import rest
    source = inspect.getsource(rest)

    # Buscar la línea problemática que inyecta "⚙️ (back office)" en la conversación
    assert '⚙️ (back office)' not in source and '(back office)' not in source, \
        "rest.py inyecta mensajes 'back office' en la conversación del usuario"


def test_backoffice_logs_separately():
    """El back-office debe loguear en EventLog, no en la conversación."""
    import inspect
    from agentic_os.interfaces.api import rest
    source = inspect.getsource(rest)

    # El back-office debe usar EventLog, no _append_message_to_conversation
    assert "BackgroundProcessingDone" in source or "BackgroundProcessingFailed" in source, \
        "El back-office debe emitir eventos EventLog separados"


def test_chat_response_is_only_from_front_assistant():
    """La respuesta del chat SOLO debe venir del FrontAssistant, no del orquestrador."""
    import inspect
    from agentic_os.interfaces.api import rest
    source = inspect.getsource(rest.chat)

    # La respuesta del chat debe ser solo del front_assistant
    assert "front_assistant.answer" in source or "_front_assistant.answer" in source, \
        "La respuesta del chat debe venir del FrontAssistant"
    # No debe haber mezcla de respuestas del orquestrador en el reply
    assert "orchestrator" not in source.lower() or "task_id" in source, \
        "El orchestrator no debe mezclarse en la respuesta del chat"
