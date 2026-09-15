"""tests.interfaces.test_supabase_jwt_auth: verificacion JWT en REST API."""

import pytest
from unittest.mock import MagicMock, patch


class TestSupabaseJWTAuth:

    @patch("agentic_os.interfaces.api.rest._tenant_registry")
    @patch("agentic_os.interfaces.api.rest._verify_supabase_jwt")
    def test_tenant_scope_con_jwt_valido(self, mock_verify, mock_registry):
        mock_verify.return_value = (
            {
                "tenant_id": "tenant-1",
                "user_id": "user-1",
                "org_role": "admin",
            },
            "valid",
        )
        mock_tenant = MagicMock()
        mock_tenant.id = "tenant-1"
        mock_tenant.config.credentials_expires_at = None
        mock_registry.get.return_value = mock_tenant
        from agentic_os.interfaces.api.rest import tenant_scope
        result = tenant_scope(
            x_tenant_id=None,
            x_api_key=None,
            x_admin_key=None,
            authorization="Bearer mock-token",
        )
        assert result == "tenant-1"

    @patch("agentic_os.interfaces.api.rest._verify_supabase_jwt")
    def test_tenant_scope_con_jwt_sin_tenant_id(self, mock_verify):
        mock_verify.return_value = ({"user_id": "user-1"}, "valid")
        from agentic_os.interfaces.api.rest import tenant_scope
        result = tenant_scope(
            x_tenant_id=None,
            x_api_key=None,
            x_admin_key=None,
            authorization="Bearer mock-token",
        )
        assert result == "system"

    def test_verify_supabase_jwt_sin_header(self):
        from agentic_os.interfaces.api.rest import _verify_supabase_jwt
        result, state = _verify_supabase_jwt(None)
        assert result is None
        assert state.value == "no_token"
        result, state = _verify_supabase_jwt("")
        assert result is None
        assert state.value == "no_token"
        result, state = _verify_supabase_jwt("Basic abc")
        assert result is None
        assert state.value == "no_token"
