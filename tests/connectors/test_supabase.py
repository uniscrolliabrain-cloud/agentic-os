"""tests.connectors.test_supabase: Supabase connector."""

import pytest
from unittest.mock import MagicMock, patch

from agentic_os.connectors.providers.supabase import SupabaseConnector
from agentic_os.connectors.core.models import Command


class TestSupabaseConnector:

    def test_connector_nace_sin_conectar(self):
        conn = SupabaseConnector()
        assert conn.connected is False
        assert conn.connector_id == "supabase"
        assert conn.provider == "Supabase"
        assert len(conn.capabilities) > 0

    @pytest.mark.asyncio
    async def test_execute_sin_conectar_da_not_configured(self):
        conn = SupabaseConnector()
        cmd = Command(capability="storage.file.read", params={})
        result = await conn.execute(cmd)
        assert result.ok is False
        assert result.error_type == "CONNECTOR_NOT_CONFIGURED"

    @pytest.mark.asyncio
    async def test_health_check_sin_credenciales(self):
        conn = SupabaseConnector()
        health = await conn.health_check()
        assert health.status == "AUTH_REQUIRED"

    @pytest.mark.asyncio
    async def test_validate_credentials_sin_conectar(self):
        conn = SupabaseConnector()
        cred = await conn.validate_credentials()
        assert cred.status == "missing"

    @pytest.mark.asyncio
    async def test_execute_dry_run_con_conexion(self):
        conn = SupabaseConnector(
            connected=True,
            credentials={"url": "https://test.supabase.co", "key": "test-key"},
        )
        conn._client = MagicMock()
        cmd = Command(
            capability="storage.file.upload",
            params={"bucket": "test", "path": "file.txt"},
            dry_run=True,
        )
        result = await conn.execute(cmd)
        assert result.dry_run is True
        assert result.preview is not None

    @pytest.mark.asyncio
    @patch("agentic_os.connectors.providers.supabase.SupabaseConnector._get_client")
    async def test_health_check_con_conexion(self, mock_get):
        mock_get.return_value = MagicMock()
        conn = SupabaseConnector(
            connected=True,
            credentials={"url": "https://test.supabase.co", "key": "test-key"},
        )
        health = await conn.health_check()
        assert health.status == "HEALTHY"

    @pytest.mark.asyncio
    @patch("agentic_os.connectors.providers.supabase.SupabaseConnector._get_client")
    async def test_storage_upload(self, mock_get):
        mock_client = MagicMock()
        mock_storage = MagicMock()
        type(mock_storage).from_ = MagicMock()
        mock_client.storage = mock_storage
        mock_get.return_value = mock_client
        conn = SupabaseConnector(
            connected=True,
            credentials={"url": "https://test.supabase.co", "key": "test-key"},
        )
        cmd = Command(
            capability="storage.file.upload",
            params={"bucket": "my-bucket", "path": "data/file.txt", "file": b"content"},
        )
        result = await conn.execute(cmd)
        assert result.ok is True

    @pytest.mark.asyncio
    @patch("agentic_os.connectors.providers.supabase.SupabaseConnector._get_client")
    async def test_storage_download(self, mock_get):
        mock_client = MagicMock()
        mock_storage = MagicMock()
        type(mock_storage).from_ = MagicMock()
        mock_client.storage = mock_storage
        mock_get.return_value = mock_client
        conn = SupabaseConnector(
            connected=True,
            credentials={"url": "https://test.supabase.co", "key": "test-key"},
        )
        cmd = Command(
            capability="storage.file.download",
            params={"bucket": "b", "path": "p"},
        )
        result = await conn.execute(cmd)
        assert result.ok is True

    @pytest.mark.asyncio
    @patch("agentic_os.connectors.providers.supabase.SupabaseConnector._get_client")
    async def test_auth_signin(self, mock_get):
        mock_auth = MagicMock()
        mock_auth.sign_in_with_password.return_value = MagicMock(
            user={"id": "u1", "email": "test@test.com"},
            access_token="token-123",
        )
        mock_client = MagicMock()
        mock_client.auth = mock_auth
        mock_get.return_value = mock_client
        conn = SupabaseConnector(
            connected=True,
            credentials={"url": "https://test.supabase.co", "key": "test-key"},
        )
        cmd = Command(
            capability="auth.signin.email",
            params={"email": "test@test.com", "password": "pass"},
        )
        result = await conn.execute(cmd)
        assert result.ok is True

    @pytest.mark.asyncio
    @patch("agentic_os.connectors.providers.supabase.SupabaseConnector._get_client")
    async def test_unknown_capability(self, mock_get):
        mock_get.return_value = MagicMock()
        conn = SupabaseConnector(
            connected=True,
            credentials={"url": "https://test.supabase.co", "key": "test-key"},
        )
        cmd = Command(capability="unknown.op", params={})
        result = await conn.execute(cmd)
        assert result.ok is False

    @pytest.mark.asyncio
    @patch("agentic_os.connectors.providers.supabase.SupabaseConnector._get_client")
    async def test_db_record_delete(self, mock_get):
        mock_db = MagicMock()
        mock_db.table.return_value.delete.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"id": 1}]
        )
        mock_client = MagicMock()
        mock_client.db = mock_db
        mock_get.return_value = mock_client
        conn = SupabaseConnector(
            connected=True,
            credentials={"url": "https://test.supabase.co", "key": "test-key"},
        )
        cmd = Command(
            capability="db.record.delete",
            params={"table": "users", "filters": {"active": True}},
        )
        result = await conn.execute(cmd)
        assert result.ok is True

    @pytest.mark.asyncio
    @patch("agentic_os.connectors.providers.supabase.SupabaseConnector._get_client")
    async def test_db_record_read(self, mock_get):
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.eq.return_value = mock_query
        mock_query.execute.return_value = MagicMock(
            data=[{"id": 1}, {"id": 2}]
        )
        mock_db.table.return_value.select.return_value = mock_query
        mock_client = MagicMock()
        mock_client.db = mock_db
        mock_get.return_value = mock_client
        conn = SupabaseConnector(
            connected=True,
            credentials={"url": "https://test.supabase.co", "key": "test-key"},
        )
        cmd = Command(
            capability="db.record.read",
            params={"table": "users", "filters": {"active": True}},
        )
        result = await conn.execute(cmd)
        assert result.ok is True
        assert len(result.output["data"]) == 2

    @pytest.mark.asyncio
    @patch("agentic_os.connectors.providers.supabase.SupabaseConnector._get_client")
    async def test_db_schema_inspect(self, mock_get):
        mock_db = MagicMock()
        mock_db.table.return_value.select.return_value.execute.return_value = MagicMock(
            data=[{"table_name": "users"}, {"table_name": "events"}]
        )
        mock_client = MagicMock()
        mock_client.db = mock_db
        mock_get.return_value = mock_client
        conn = SupabaseConnector(
            connected=True,
            credentials={"url": "https://test.supabase.co", "key": "test-key"},
        )
        cmd = Command(capability="db.schema.inspect")
        result = await conn.execute(cmd)
        assert result.ok is True
        assert len(result.output["tables"]) == 2
