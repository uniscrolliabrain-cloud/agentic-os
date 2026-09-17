"""Bug 15 - Reloj no canónico Webhook: datetime.now(timezone.utc) en vez de now_utc()"""

import pytest


def test_webhook_uses_canonical_time():
    """El módulo de webhooks debe usar now_utc() canónico, no datetime.now()."""
    import inspect
    from agentic_os.connectors.webhook import WebhookReceiver, WebhookValidator

    for cls in [WebhookReceiver, WebhookValidator]:
        source = inspect.getsource(cls)
        assert "datetime.now(timezone.utc)" not in source, \
            f"{cls.__name__} usa datetime.now() en vez de now_utc()"


def test_webhook_event_uses_canonical_time():
    """WebhookEvent debe usar now_utc() para received_at."""
    import inspect
    from agentic_os.connectors.webhook import WebhookEvent
    source = inspect.getsource(WebhookEvent)
    # Debe importar now_utc o usar default_factory con now_utc
    assert "now_utc" in source or "datetime.now(timezone.utc)" not in source, \
        "WebhookEvent no usa now_utc() canónico"


def test_all_modules_use_canonical_time():
    """Todos los módulos del proyecto deben usar now_utc(), no datetime.now()."""
    import inspect
    from agentic_os.connectors.webhook import WebhookEvent
    source = inspect.getsource(WebhookEvent)
    # Verificar que no hay datetime.now(timezone.utc) directo
    if "datetime.now(timezone.utc)" in source:
        pytest.fail("WebhookEvent usa datetime.now(timezone.utc) en vez de now_utc()")
