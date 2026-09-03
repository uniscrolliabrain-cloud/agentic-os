"""Tests para el modelo canónico WebhookEvent (Pydantic v2)."""
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from agentic_os.connectors.webhook import WebhookEvent


def test_webhook_event_basic_fields():
    event = WebhookEvent(
        event_id="evt-1",
        event_type="test",
        payload={"foo": "bar"},
    )
    assert event.event_id == "evt-1"
    assert event.event_type == "test"
    assert event.payload == {"foo": "bar"}
    # `received_at` se autocompleta con un datetime tz-aware (clase real)
    assert event.received_at is not None
    assert event.received_at.tzinfo is not None


def test_webhook_event_is_real_pydantic_model():
    # Campo obligatorio faltante -> error de validación real de Pydantic
    with pytest.raises(ValidationError):
        WebhookEvent(event_type="test", payload={})

    # Campo inesperado -> rechazado por extra="forbid"
    with pytest.raises(ValidationError):
        WebhookEvent(
            event_id="evt-1",
            event_type="test",
            payload={},
            provider="x",
            unexpected="boom",
        )


def test_webhook_event_is_frozen():
    event = WebhookEvent(event_id="evt-1", event_type="test", payload={})
    with pytest.raises((TypeError, ValidationError)):
        event.event_id = "mutated"


def test_webhook_event_payload_default_is_independent():
    a = WebhookEvent(event_id="a", event_type="t")
    b = WebhookEvent(event_id="b", event_type="t")
    assert a.payload == {} and b.payload == {}
    a.payload["k"] = "v"
    assert b.payload == {}
