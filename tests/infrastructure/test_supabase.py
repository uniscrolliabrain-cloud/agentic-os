"""tests.infrastructure.test_supabase_client: Supabase client e event log."""

import pytest
from unittest.mock import MagicMock, patch

from agentic_os.infrastructure.supabase_client import SupabaseClient


class TestSupabaseClient:

    def test_get_returns_singleton(self, monkeypatch):
        monkeypatch.setattr(
            "agentic_os.infrastructure.supabase_client.settings",
            MagicMock(supabase_url="https://test.supabase.co", supabase_key="test-key"),
        )
        SupabaseClient._instance = None
        client = SupabaseClient.get()
        assert isinstance(client, SupabaseClient)
        assert SupabaseClient.get() is client

    def test_get_raises_without_config(self, monkeypatch):
        SupabaseClient._instance = None
        with pytest.raises(RuntimeError):
            SupabaseClient.get()

    def test_reset_clears_singleton(self):
        SupabaseClient._instance = MagicMock()
        SupabaseClient.reset()
        assert SupabaseClient._instance is None


class TestSupabaseEventLog:

    @pytest.mark.asyncio
    async def test_degrada_a_jsonl_sin_supabase(self, tmp_path):
        from agentic_os.infrastructure.persistence.supabase import SupabaseEventLog
        from agentic_os.kernel.world.events import Event
        log = SupabaseEventLog(base_dir=str(tmp_path / "eventlog"))
        assert log.available is False
        e = Event(kind="test", entity_id="x", tenant_id="tenant-a")
        log.append(e)
        assert len(log.list_for_tenant("tenant-a")) == 1

    @pytest.mark.asyncio
    @patch("agentic_os.infrastructure.persistence.supabase.get_supabase")
    async def test_append_con_supabase(self, mock_get):
        mock_table = MagicMock()
        mock_db = MagicMock()
        mock_db.table.return_value = mock_table
        mock_get.return_value = MagicMock(db=mock_db)

        from agentic_os.infrastructure.persistence.supabase import SupabaseEventLog
        from agentic_os.kernel.world.events import Event
        log = SupabaseEventLog()
        assert log.available is True
        e = Event(kind="test", entity_id="x", tenant_id="tenant-a")
        log.append(e)
        mock_db.table.assert_called_once()

    @pytest.mark.asyncio
    @patch("agentic_os.infrastructure.persistence.supabase.get_supabase")
    async def test_list_for_tenant(self, mock_get):
        mock_table = MagicMock()
        mock_table.select.return_value.eq.return_value.order.return_value.execute.return_value = MagicMock(
            data=[{"id": "1", "kind": "test", "entity_id": "x", "tenant_id": "t1", "payload": {}, "at": "2024-01-01T00:00:00", "actor_id": None, "correlation_id": None, "command_id": None}]
        )
        mock_db = MagicMock()
        mock_db.table.return_value = mock_table
        mock_get.return_value = MagicMock(db=mock_db)

        from agentic_os.infrastructure.persistence.supabase import SupabaseEventLog
        log = SupabaseEventLog()
        events = log.list_for_tenant("t1")
        mock_db.table.assert_called_once()
