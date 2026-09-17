from __future__ import annotations

import asyncio
import os
import pytest

from agentic_os.connectors.core.http import HttpClient, _safe_headers
from agentic_os.execution.tools.base import ToolValidationError
from agentic_os.infrastructure.config.settings import Settings


# ============================================================================
# Bug #1 Tests - HttpClient (SSRF, Timeouts, Session Cleanup, Redaction)
# ============================================================================

def test_http_client_redacts_sensitive_headers():
    headers = {
        "Authorization": "Bearer secret-token-123",
        "Cookie": "session=abc456",
        "api_key": "my-secret-key",
        "Content-Type": "application/json",
    }
    safe = _safe_headers(headers)
    assert safe["Authorization"] == "***REDACTED***"
    assert safe["Cookie"] == "***REDACTED***"
    assert safe["api_key"] == "***REDACTED***"
    assert safe["Content-Type"] == "application/json"


@pytest.mark.anyio
async def test_http_client_context_manager_session_lifecycle():
    client = HttpClient(timeout_s=15.0, retries=2)
    assert client._client is None
    async with client as c:
        assert c._client is not None
        assert not c._client.is_closed
    assert client._client is None


def test_http_client_timeout_and_config():
    client = HttpClient(timeout_s=5.0, retries=5)
    assert client.timeout == 5.0
    assert client.retries == 5


@pytest.mark.anyio
async def test_http_client_ssrf_blocking_local_and_private_ips():
    client = HttpClient()
    
    # Target URLs pointing to localhost and private networks
    blocked_urls = [
        "http://127.0.0.1/admin",
        "http://localhost:8080/metrics",
        "http://169.254.169.254/latest/meta-data/",
        "http://0.0.0.0/",
        "http://[::1]/status",
    ]

    for url in blocked_urls:
        with pytest.raises(ToolValidationError, match="SSRF blocked"):
            await client.request("GET", url)


# ============================================================================
# Bug #2 Tests - Settings (Secrets Redaction & Production Validation)
# ============================================================================

def test_settings_loads_from_env(monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "valid_admin_key_789")
    monkeypatch.setenv("CREDENTIAL_ENCRYPTION_KEY", "valid_encryption_key_456")
    monkeypatch.setenv("ENV", "staging")
    cfg = Settings(_env_file=None)
    assert cfg.admin_api_key == "valid_admin_key_789"
    assert cfg.credential_encryption_key == "valid_encryption_key_456"
    assert cfg.env == "staging"


def test_settings_fails_in_production_without_encryption_key(monkeypatch):
    monkeypatch.setenv("ENV", "production")
    monkeypatch.delenv("CREDENTIAL_ENCRYPTION_KEY", raising=False)
    with pytest.raises(ValueError, match="CREDENTIAL_ENCRYPTION_KEY"):
        Settings(_env_file=None)


def test_settings_allows_dev_without_encryption_key(monkeypatch):
    monkeypatch.setenv("ENV", "dev")
    monkeypatch.delenv("CREDENTIAL_ENCRYPTION_KEY", raising=False)
    cfg = Settings(_env_file=None)  # no debe lanzar en dev (ver PRE_PRODUCTION_CHECKLIST.md #1)
    assert cfg.credential_encryption_key is None


def test_settings_redacts_secrets_in_repr_and_str(monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "super_secret_admin_key")
    monkeypatch.setenv("CREDENTIAL_ENCRYPTION_KEY", "super_secret_encryption_key")
    monkeypatch.setenv("STRIPE_SECRET_KEY", "super_secret_stripe_key")
    cfg = Settings(_env_file=None)

    repr_str = repr(cfg)
    str_str = str(cfg)

    assert "super_secret_admin_key" not in repr_str
    assert "super_secret_encryption_key" not in repr_str
    assert "super_secret_stripe_key" not in repr_str
    assert "***REDACTED***" in repr_str

    assert "super_secret_admin_key" not in str_str
    assert "super_secret_encryption_key" not in str_str
    assert "super_secret_stripe_key" not in str_str
    assert "***REDACTED***" in str_str
