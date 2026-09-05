"""Tests del routing REAL de Google a través del Connector Kernel (mock-based).

Verifican que:
- Sin GOOGLE_REAL → el registry registra el StubConnector (comportamiento histórico).
- Con GOOGLE_REAL + credenciales → el registry registra el GoogleConnector REAL
  y las caps residuales (video/analytics) van a un stub 'google-extra'.
- Los Commands (Pydantic) fluyen por ConnectorRouter hasta los adapters reales
  (mockeados aqui): los LLM nunca tocan el conector directamente.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from agentic_os.connectors.core.models import Command
from agentic_os.connectors.router import ConnectorRouter
from agentic_os.execution.tools.connector_bridge import (
    build_capability_registry,
    build_connector_router,
)
from agentic_os.infrastructure.config.settings import settings


def _router_with_fakes(monkeypatch) -> ConnectorRouter:
    """Registry con GoogleConnector real + adapters fake, sin reconstruir nada."""
    _fake_settings(monkeypatch, real=True)
    registry = build_capability_registry()
    _install_fake_adapters(registry.get_connector("google"))
    return ConnectorRouter(registry)


# ----------------------------------------------------------------- fakes ---
class FakeGmail:
    def list_messages(self, max_results=10, query=None):
        return [{"id": "m1", "snippet": "hola"}]

    def get_message(self, message_id):
        return {"id": message_id, "subject": "test", "body": "hola"}

    def send_message(self, to, subject="", body="", from_addr=None):
        return {"id": "sent-1", "thread_id": "t1", "label_ids": ["SENT"]}


class FakeDrive:
    def read_file(self, file_id):
        return {"id": file_id, "content": "contenido"}

    def list_files(self, folder_id=None):
        return [{"id": "f1", "name": "a.txt"}]

    def create_file(self, name="untitled.txt", content="", mime_type="text/plain", folder_id=None):
        return {"id": "fake-file-id", "name": name, "mime_type": mime_type}


class FakeCalendar:
    def create_event(self, title, start, end, attendees=None):
        return {"id": "ev1", "summary": title, "link": "http://cal/ev1"}

    def list_events(self, max_results=10, time_min=None):
        return [{"id": "ev1", "title": "Reunion", "start": start, "end": end}]


def _fake_settings(monkeypatch, real: bool):
    monkeypatch.setattr(settings, "google_real", real)
    monkeypatch.setattr(settings, "google_client_id", "fake-id.apps.googleusercontent.com")
    monkeypatch.setattr(settings, "google_client_secret", "GOCSPX-fake")
    monkeypatch.setattr(settings, "google_refresh_token", "1//fake-refresh-token")


def _install_fake_adapters(conn) -> None:
    conn._gmail = FakeGmail()
    conn._drive = FakeDrive()
    conn._calendar = FakeCalendar()


# ------------------------------------------------------------------ tests ---
def test_sin_flag_registra_stub(monkeypatch):
    """Sin GOOGLE_REAL, google sigue siendo StubConnector (default seguro)."""
    _fake_settings(monkeypatch, real=False)
    registry = build_capability_registry()
    conn = registry.get_connector("google")
    assert conn is not None
    assert type(conn).__name__ == "StubConnector", (
        "Sin GOOGLE_REAL el connector google debe ser stub"
    )
    for cap in ("email.message.send", "file.create", "calendar.event.create"):
        assert registry.has_capability(cap)


def test_con_flag_registra_real_y_stub_residual(monkeypatch):
    """Con GOOGLE_REAL: google real para las 6 caps, stub residual para el resto."""
    _fake_settings(monkeypatch, real=True)
    registry = build_capability_registry()
    real = registry.get_connector("google")
    assert type(real).__name__ == "GoogleConnector"
    assert real.connected is True
    assert set(real.capabilities) == {
        "email.message.read", "email.message.send",
        "file.read", "file.create",
        "calendar.event.create", "calendar.event.read",
    }
    residual = registry.get_connector("google-extra")
    assert residual is not None
    assert set(residual.capabilities) == {
        "video.upload", "analytics.metrics.get", "analytics.search.query",
    }


def test_flag_sin_credenciales_cae_en_stub(monkeypatch):
    """GOOGLE_REAL=true pero sin credenciales → stub (gate doble)."""
    _fake_settings(monkeypatch, real=True)
    monkeypatch.setattr(settings, "google_client_id", None)
    registry = build_capability_registry()
    conn = registry.get_connector("google")
    assert type(conn).__name__ == "StubConnector"


# ------------------------------------------------------------ routing real ---
@pytest.mark.asyncio
async def test_routing_real_drive_create(monkeypatch):
    """Command file.create → ConnectorRouter → GoogleConnector → adapter Drive."""
    router = _router_with_fakes(monkeypatch)

    result = await router.route(
        Command(capability="file.create", params={"name": "informe.txt", "content": "hola"})
    )
    assert result.ok is True
    assert result.provider == "google"
    assert result.output["id"] == "fake-file-id"
    assert result.output["name"] == "informe.txt"


@pytest.mark.asyncio
async def test_routing_real_gmail_send(monkeypatch):
    router = _router_with_fakes(monkeypatch)

    result = await router.route(
        Command(
            capability="email.message.send",
            params={"to": "cliente@ejemplo.com", "subject": "Hola", "body": "Mensaje"},
        )
    )
    assert result.ok is True
    assert result.output["id"] == "sent-1"


@pytest.mark.asyncio
async def test_routing_real_gmail_read(monkeypatch):
    router = _router_with_fakes(monkeypatch)

    result = await router.route(Command(capability="email.message.read", params={}))
    assert result.ok is True
    assert isinstance(result.output, list)
    assert result.output[0]["id"] == "m1"


@pytest.mark.asyncio
async def test_routing_real_calendar_create(monkeypatch):
    router = _router_with_fakes(monkeypatch)

    result = await router.route(
        Command(
            capability="calendar.event.create",
            params={
                "title": "Reunion cliente",
                "start": "2026-09-05T10:00:00Z",
                "end": "2026-09-05T11:00:00Z",
            },
        )
    )
    assert result.ok is True
    assert result.output["summary"] == "Reunion cliente"


@pytest.mark.asyncio
async def test_routing_caps_residuales_van_al_stub(monkeypatch):
    """video.upload no tiene adapter real: va al stub residual y falla limpio."""
    _fake_settings(monkeypatch, real=True)
    registry = build_capability_registry()
    residual = registry.get_connector("google-extra")
    assert residual is not None
    router = build_connector_router()

    result = await router.route(Command(capability="video.upload", params={"title": "x"}))
    assert result.ok is False  # stub sin credenciales conectadas no ejecuta nada


@pytest.mark.asyncio
async def test_routing_capability_desconocida_falla_limpio(monkeypatch):
    _fake_settings(monkeypatch, real=True)
    registry = build_capability_registry()
    _install_fake_adapters(registry.get_connector("google"))
    router = build_connector_router()

    result = await router.route(Command(capability="capacidad.inexistente", params={}))
    assert result.ok is False
    assert result.error_type in ("UNSUPPORTED_CAPABILITY", "UNSUPPORTED_OPERATION")


def test_command_pydantic_rechaza_params_invalidos():
    """Los LLM pasan por el modelo Pydantic Command: capability debe ser str
    y el Command es inmutable (frozen) — nadie muta un comando en vuelo."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        Command(capability=123, params={})
    cmd = Command(capability="file.create", params={"name": "x"})
    with pytest.raises(ValidationError):
        cmd.params = {}  # frozen: mutación prohibida
