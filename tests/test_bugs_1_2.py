from __future__ import annotations

import asyncio
import os
import pytest

from agentic_os.connectors.core.http import HttpClient, _safe_headers
from agentic_os.core.config import Config
from agentic_os.execution.tools.base import ToolValidationError


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
# Bug #2 Tests - Config (Secrets Redaction & Env Loading)
# ============================================================================

def test_config_loads_from_env():
    env = {
        "API_KEY": "valid_api_key_123",
        "SECRET_KEY": "valid_secret_key_456",
        "ADMIN_KEY": "valid_admin_key_789",
        "ENV": "staging",
        "DEBUG": "true",
    }
    cfg = Config(env=env)
    assert cfg.api_key == "valid_api_key_123"
    assert cfg.secret_key == "valid_secret_key_456"
    assert cfg.admin_key == "valid_admin_key_789"
    assert cfg.env == "staging"
    assert cfg.debug is True


def test_config_fails_when_secrets_missing():
    # Environment missing SECRET_KEY
    env = {"API_KEY": "valid_api_key_123"}
    with pytest.raises(ValueError, match="Missing required secret environment variable"):
        Config(env=env)


def test_config_redacts_secrets_in_repr_and_str():
    env = {
        "API_KEY": "super_secret_api_key",
        "SECRET_KEY": "super_secret_jwt_key",
        "ADMIN_KEY": "super_secret_admin_key",
    }
    cfg = Config(env=env)
    
    repr_str = repr(cfg)
    str_str = str(cfg)
    
    assert "super_secret_api_key" not in repr_str
    assert "super_secret_jwt_key" not in repr_str
    assert "super_secret_admin_key" not in repr_str
    assert "***REDACTED***" in repr_str
    
    assert "super_secret_api_key" not in str_str
    assert "super_secret_jwt_key" not in str_str
    assert "super_secret_admin_key" not in str_str
    assert "***REDACTED***" in str_str
