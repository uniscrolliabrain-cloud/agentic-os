"""Tests de integración para adapters Google (Gmail, Drive, Calendar)."""
import base64
import json
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import httpx
import pytest

from agentic_os.connectors.adapters.google_auth import GoogleAuth, MissingCredentials
from agentic_os.connectors.adapters.google_gmail import GoogleGmailAdapter
from agentic_os.connectors.adapters.google_drive import GoogleDriveAdapter
from agentic_os.connectors.adapters.google_calendar import GoogleCalendarAdapter
from agentic_os.connectors.core.errors import AuthenticationError, NotFoundError, ProviderError


@pytest.fixture
def mock_settings():
    settings = MagicMock()
    settings.google_client_id = "test-client-id.apps.googleusercontent.com"
    settings.google_client_secret = "GOCSPX-test-secret"
    settings.google_refresh_token = "test-refresh-token"
    settings.google_redirect_uri = "http://localhost:8000/oauth/callback"
    return settings


@pytest.fixture
def mock_auth(mock_settings):
    with patch.object(GoogleAuth, "__init__", lambda self, settings=None: None):
        auth = GoogleAuth.__new__(GoogleAuth)
        auth._settings = mock_settings
        auth._lock = __import__("threading").Lock()
        auth._access_token = "test-access-token"
        auth._expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        yield auth


def _make_response(status_code=200, json_data=None, text=""):
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.json.return_value = json_data or {}
    resp.text = text or json.dumps(json_data or {})
    if status_code >= 400:
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            f"Error {status_code}", request=MagicMock(), response=resp
        )
    else:
        resp.raise_for_status.return_value = None
    return resp

class TestGoogleGmailAdapter:
    def test_list_messages_success(self, mock_auth):
        adapter = GoogleGmailAdapter(mock_auth)
        with patch.object(adapter._client, "request") as mock_req:
            mock_req.return_value = _make_response(200, {
                "messages": [{"id": "msg1", "threadId": "t1", "snippet": "Hola"}]
            })
            result = adapter.list_messages(max_results=10)
            assert len(result) == 1
            assert result[0]["id"] == "msg1"

    def test_list_messages_empty(self, mock_auth):
        adapter = GoogleGmailAdapter(mock_auth)
        with patch.object(adapter._client, "request") as mock_req:
            mock_req.return_value = _make_response(200, {})
            assert adapter.list_messages() == []

    def test_get_message_full(self, mock_auth):
        adapter = GoogleGmailAdapter(mock_auth)
        body_b64 = base64.urlsafe_b64encode(b"Hola Mundo").decode()
        with patch.object(adapter._client, "request") as mock_req:
            mock_req.return_value = _make_response(200, {
                "id": "msg1", "threadId": "t1",
                "payload": {
                    "headers": [{"name": "From", "value": "a@b.com"}, {"name": "Subject", "value": "Test"}],
                    "parts": [{"mimeType": "text/plain", "body": {"data": body_b64}}],
                },
                "snippet": "snip",
            })
            result = adapter.get_message("msg1")
            assert result["from"] == "a@b.com"
            assert result["body"] == "Hola Mundo"

    def test_send_message_success(self, mock_auth):
        adapter = GoogleGmailAdapter(mock_auth)
        with patch.object(adapter._client, "request") as mock_req:
            mock_req.return_value = _make_response(200, {"id": "sent-id", "threadId": "t1", "labelIds": ["SENT"]})
            result = adapter.send_message(to="x@y.com", subject="S", body="B")
            assert result["id"] == "sent-id"

    def test_auth_error_401(self, mock_auth):
        adapter = GoogleGmailAdapter(mock_auth)
        with patch.object(adapter._client, "request") as mock_req:
            mock_req.return_value = _make_response(401, text="Unauthorized")
            with pytest.raises(AuthenticationError):
                adapter.list_messages()

    def test_not_found_404(self, mock_auth):
        adapter = GoogleGmailAdapter(mock_auth)
        with patch.object(adapter._client, "request") as mock_req:
            mock_req.return_value = _make_response(404, text="Not Found")
            with pytest.raises(NotFoundError):
                adapter.get_message("bad-id")

class TestGoogleDriveAdapter:
    def test_list_files_success(self, mock_auth):
        adapter = GoogleDriveAdapter(mock_auth)
        with patch.object(adapter._client, "request") as mock_req:
            mock_req.return_value = _make_response(200, {
                "files": [{"id": "f1", "name": "doc.txt", "size": "1024", "mimeType": "text/plain", "modifiedTime": "2024-01-01T00:00:00Z"}]
            })
            result = adapter.list_files()
            assert len(result) == 1
            assert result[0]["name"] == "doc.txt"

    def test_list_files_with_folder(self, mock_auth):
        adapter = GoogleDriveAdapter(mock_auth)
        with patch.object(adapter._client, "request") as mock_req:
            mock_req.return_value = _make_response(200, {"files": []})
            adapter.list_files(folder_id="folder123")
            call_args = mock_req.call_args
            assert "folder123" in call_args[1].get("params", {}).get("q", "")

    def test_read_file_text(self, mock_auth):
        adapter = GoogleDriveAdapter(mock_auth)
        with patch.object(adapter._client, "request") as mock_req,              patch.object(adapter._client, "get") as mock_get:
            mock_req.return_value = _make_response(200, {"id": "f1", "name": "d.txt", "mimeType": "text/plain"})
            mock_get.return_value = _make_response(200, text="Contenido")
            result = adapter.read_file("f1")
            assert result["content"] == "Contenido"

    def test_create_file_success(self, mock_auth):
        adapter = GoogleDriveAdapter(mock_auth)
        with patch.object(adapter._client, "post") as mock_post:
            mock_post.return_value = _make_response(200, {"id": "new-id", "name": "t.txt", "mimeType": "text/plain"})
            result = adapter.create_file(name="t.txt", content="Hola")
            assert result["id"] == "new-id"

    def test_search_files(self, mock_auth):
        adapter = GoogleDriveAdapter(mock_auth)
        with patch.object(adapter._client, "request") as mock_req:
            mock_req.return_value = _make_response(200, {
                "files": [{"id": "f1", "name": "rep.pdf", "mimeType": "application/pdf"}]
            })
            result = adapter.search("rep")
            assert len(result) == 1

    def test_auth_error_403(self, mock_auth):
        adapter = GoogleDriveAdapter(mock_auth)
        with patch.object(adapter._client, "request") as mock_req:
            mock_req.return_value = _make_response(403, text="Forbidden")
            with pytest.raises(AuthenticationError):
                adapter.list_files()

class TestGoogleCalendarAdapter:
    def test_create_event_success(self, mock_auth):
        adapter = GoogleCalendarAdapter(mock_auth)
        with patch.object(adapter._client, "request") as mock_req:
            mock_req.return_value = _make_response(200, {
                "id": "e1", "summary": "Reunion",
                "start": {"dateTime": "2024-01-01T10:00:00Z"},
                "end": {"dateTime": "2024-01-01T11:00:00Z"},
                "htmlLink": "https://calendar.google.com/e1",
            })
            result = adapter.create_event(title="Reunion", start="2024-01-01T10:00:00Z", end="2024-01-01T11:00:00Z")
            assert result["id"] == "e1"
            assert result["summary"] == "Reunion"

    def test_create_event_with_attendees(self, mock_auth):
        adapter = GoogleCalendarAdapter(mock_auth)
        with patch.object(adapter._client, "request") as mock_req:
            mock_req.return_value = _make_response(200, {
                "id": "e1", "summary": "R",
                "start": {"dateTime": "2024-01-01T10:00:00Z"},
                "end": {"dateTime": "2024-01-01T11:00:00Z"},
                "htmlLink": "",
            })
            adapter.create_event(title="R", start="s", end="e", attendees=["a@b.com", "c@d.com"])
            call_body = mock_req.call_args[1].get("json", {})
            assert len(call_body.get("attendees", [])) == 2

    def test_list_events_success(self, mock_auth):
        adapter = GoogleCalendarAdapter(mock_auth)
        with patch.object(adapter._client, "request") as mock_req:
            mock_req.return_value = _make_response(200, {
                "items": [{"id": "e1", "summary": "Ev1", "start": {"dateTime": "2024-01-01T10:00:00Z"}, "end": {"dateTime": "2024-01-01T11:00:00Z"}}]
            })
            result = adapter.list_events(max_results=10)
            assert len(result) == 1
            assert result[0]["title"] == "Ev1"

    def test_list_events_uses_now_utc_default(self, mock_auth):
        adapter = GoogleCalendarAdapter(mock_auth)
        with patch.object(adapter._client, "request") as mock_req:
            mock_req.return_value = _make_response(200, {"items": []})
            adapter.list_events()
            call_params = mock_req.call_args[1].get("params", {})
            assert "timeMin" in call_params

    def test_provider_error_400(self, mock_auth):
        adapter = GoogleCalendarAdapter(mock_auth)
        with patch.object(adapter._client, "request") as mock_req:
            mock_req.return_value = _make_response(400, text="Bad")
            with pytest.raises(ProviderError):
                adapter.create_event(title="X", start="bad", end="bad")

class TestGoogleAuth:
    def test_access_token_valid_not_refreshed(self, mock_settings):
        with patch.object(GoogleAuth, "__init__", lambda self, settings=None: None):
            auth = GoogleAuth.__new__(GoogleAuth)
            auth._settings = mock_settings
            auth._lock = __import__("threading").Lock()
            auth._access_token = "valid-token"
            auth._expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
            assert auth.access_token() == "valid-token"

    def test_access_token_expired_triggers_refresh(self, mock_settings):
        with patch.object(GoogleAuth, "__init__", lambda self, settings=None: None):
            auth = GoogleAuth.__new__(GoogleAuth)
            auth._settings = mock_settings
            auth._lock = __import__("threading").Lock()
            auth._access_token = "old-token"
            auth._expires_at = datetime.now(timezone.utc) - timedelta(minutes=5)
            with patch("agentic_os.connecters.adapters.google_auth.OAuthManager.refresh") as mock_refresh:
                mock_refresh.return_value = {"access_token": "new-token", "expires_in": 3600}
                assert auth.access_token() == "new-token"

    def test_missing_credentials_raises(self):
        settings = MagicMock()
        settings.google_client_id = None
        settings.google_refresh_token = None
        auth = GoogleAuth(settings)
        with pytest.raises(MissingCredentials):
            auth.access_token()

    def test_refresh_invalid_response_raises(self, mock_settings):
        with patch.object(GoogleAuth, "__init__", lambda self, settings=None: None):
            auth = GoogleAuth.__new__(GoogleAuth)
            auth._settings = mock_settings
            auth._lock = __import__("threading").Lock()
            auth._access_token = None
            auth._expires_at = None
            with patch("agentic_os.connecters.adapters.google_auth.OAuthManager.refresh") as mock_refresh:
                mock_refresh.return_value = {"error": "invalid_grant"}
                with pytest.raises(AuthenticationError):
                    auth.access_token()
