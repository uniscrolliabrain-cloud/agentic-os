"""Bug 7 - Doble implementación Webhooks divergente: connectors/webhook/__init__.py vs interfaces/api/webhooks.py"""

import pytest


def test_single_webhook_receiver_implementation():
    """Debe existir UNA sola implementación de WebhookReceiver, no dos divergentes."""
    # Importar de connectors/webhook
    from agentic_os.connectors.webhook import WebhookReceiver as Receiver1
    # Importar de interfaces/api
    from agentic_os.interfaces.api.webhooks import WebhookReceiver as Receiver2

    # Deben ser la misma clase o una debe envolver a la other
    # Si son clases distintas, hay divergencia
    assert Receiver1 is Receiver2 or issubclass(Receiver1, Receiver2) or issubclass(Receiver2, Receiver1), \
        "Existen dos implementaciones divergentes de WebhookReceiver"


def test_single_webhook_validator_implementation():
    """Debe existir UNA sola implementación de WebhookValidator."""
    from agentic_os.connectors.webhook import WebhookValidator as Validator1
    from agentic_os.interfaces.api.webhooks import WebhookValidator as Validator2

    assert Validator1 is Validator2 or issubclass(Validator1, Validator2) or issubclass(Validator2, Validator1), \
        "Existen dos implementaciones divergentes de WebhookValidator"


def test_webhook_receiver_uses_canonical_time():
    """WebhookReceiver debe usar now_utc() canónico, no datetime.now()."""
    from agentic_os.connectors.webhook import WebhookReceiver, WebhookValidator, WebhookRegistry
    import inspect
    source = inspect.getsource(WebhookReceiver)
    # No debe haber datetime.now(timezone.utc) directo
    assert "datetime.now(timezone.utc)" not in source, \
        "WebhookReceiver usa datetime.now() en vez de now_utc() canónico"


def test_webhook_event_uses_pydantic():
    """WebhookEvent debe ser un modelo Pydantic con validación, no un dataclass."""
    from agentic_os.connectors.webhook import WebhookEvent
    from pydantic import BaseModel
    assert issubclass(WebhookEvent, BaseModel), \
        "WebhookEvent debe ser un modelo Pydantic para validación"
