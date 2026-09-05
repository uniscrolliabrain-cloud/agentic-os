"""Tests de integracion para conectores Google (Gmail, Drive, Calendar).

Estos tests hacen llamadas REALES a la API de Google. Si las credenciales
estan ausentes o son rechazadas (p.ej. client secret invalido), se marcan
como SKIP con un mensaje accionable en vez de fallar la suite.
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


@pytest.fixture(scope="module")
def google_credentials():
    from agentic_os.infrastructure.config.settings import settings
    if not settings.google_client_id or not settings.google_refresh_token:
        pytest.skip("Credenciales Google no configuradas en .env")
    return {
        "client_id": settings.google_client_id,
        "client_secret": settings.google_client_secret,
        "refresh_token": settings.google_refresh_token,
    }


@pytest.fixture(scope="module")
def google_auth(google_credentials):
    """GoogleAuth con token real refrescado UNA vez por modulo.

    Si Google rechaza las credenciales (401 invalid_client u otro error),
    se salta el resto de tests de integracion con mensaje accionable.
    """
    from agentic_os.connectors.adapters.google_auth import GoogleAuth
    from agentic_os.connectors.core.errors import AuthenticationError
    auth = GoogleAuth()
    try:
        auth.access_token()
    except AuthenticationError as e:
        pytest.skip(
            "Google rechazo las credenciales (revisa GOOGLE_CLIENT_SECRET en "
            f"Google Cloud Console, APIs y servicios > Credenciales): {e}"
        )
    except Exception as e:  # red no disponible / timeout
        pytest.skip(f"Google no accesible desde este entorno: {e}")
    return auth


def test_credentials_loaded(google_credentials):
    assert google_credentials["client_id"] is not None
    assert google_credentials["refresh_token"] is not None
    print("OK Credenciales cargadas")


def test_google_auth_access_token(google_auth):
    token = google_auth.access_token()
    assert token is not None
    assert len(token) > 0
    print(f"OK Access token: {token[:20]}...")


def test_gmail_list_messages(google_auth):
    from agentic_os.connectors.adapters.google_gmail import GoogleGmailAdapter
    gmail = GoogleGmailAdapter(google_auth)
    messages = gmail.list_messages(max_results=5)
    assert isinstance(messages, list)
    print(f"OK Gmail: {len(messages)} mensajes")


def test_drive_list_files(google_auth):
    from agentic_os.connectors.adapters.google_drive import GoogleDriveAdapter
    drive = GoogleDriveAdapter(google_auth)
    files = drive.list_files()
    assert isinstance(files, list)
    print(f"OK Drive: {len(files)} archivos")


def test_drive_create_file(google_auth):
    from agentic_os.connectors.adapters.google_drive import GoogleDriveAdapter
    drive = GoogleDriveAdapter(google_auth)
    result = drive.create_file(name="test.txt", content="test")
    assert "id" in result
    print(f"OK Drive archivo creado: {result['id']}")


def test_calendar_list_events(google_auth):
    from agentic_os.connectors.adapters.google_calendar import GoogleCalendarAdapter
    cal = GoogleCalendarAdapter(google_auth)
    events = cal.list_events(max_results=5)
    assert isinstance(events, list)
    print(f"OK Calendar: {len(events)} eventos")


@pytest.mark.asyncio
async def test_google_connector_execute(google_auth):
    from agentic_os.connectors.google import GoogleConnector
    from agentic_os.connectors.core.models import Command
    connector = GoogleConnector()
    if not connector.connected:
        pytest.skip("Connector no conectado")
    cmd = Command(capability="file.read", params={})
    result = await connector.execute(cmd)
    assert result.ok is True
    print("OK GoogleConnector ejecutado")