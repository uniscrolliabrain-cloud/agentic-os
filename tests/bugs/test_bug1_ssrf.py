"""Bug 1 - SSRF DNS Rebinding en connectors/core/http.py: _is_ssrf() no resuelve DNS, vulnerable a dominios con TTL 0 que luego resuelven a 127.0.0.1"""

import pytest
from unittest.mock import patch
from agentic_os.connectors.core.http import HttpClient


def test_bug1_ssrf_blocks_direct_private_ips():
    """_is_ssrf debe bloquear IPs privadas/loopback directamente."""
    blocked = [
        "http://127.0.0.1/admin",
        "http://10.0.0.1/secrets",
        "http://192.168.1.1/config",
        "http://172.16.0.1/internal",
        "http://0.0.0.0/",
        "http://[::1]/status",
    ]
    for url in blocked:
        assert HttpClient._is_ssrf(url), f"SSRF no bloqueó: {url}"


def test_bug1_ssrf_blocks_alternative_ip_formats():
    """_is_ssrf debe bloquear formatos alternativos de IP (decimal, octal, hex)."""
    blocked = [
        "http://2130706433/",       # 127.0.0.1 en decimal
        "http://0177.0.0.1/",       # 127.0.0.1 en octal
        "http://0x7f000001/",       # 127.0.0.1 en hex
    ]
    for url in blocked:
        assert HttpClient._is_ssrf(url), f"SSRF no bloqueó formato alternativo: {url}"


def test_bug1_ssrf_allows_public_urls():
    """_is_ssrf NO debe bloquear URLs públicas legítimas."""
    allowed = [
        "https://api.github.com/users/octocat",
        "https://www.googleapis.com/drive/v3/files",
        "https://graph.facebook.com/v18.0/me",
    ]
    for url in allowed:
        assert not HttpClient._is_ssrf(url), f"SSRF bloqueó URL legítima: {url}"


def test_bug1_ssrf_dns_rebinding_protection():
    """_is_ssrf debe resolver DNS y bloquear si resuelve a IP privada (DNS rebinding)."""
    # Simulamos un dominio que resuelve a IP privada (DNS rebinding attack)
    with patch("agentic_os.connectors.core.http.socket.getaddrinfo") as mock_dns:
        mock_dns.return_value = [(2, 1, 6, '', ('127.0.0.1', 0))]
        # El dominio parece legítimo pero resuelve a localhost
        assert HttpClient._is_ssrf("http://evil-rebind.example.com/secret"), \
            "SSRF no detectó DNS rebinding a IP privada"


def test_bug1_ssrf_dns_resolution_failure_blocks():
    """Si DNS no se puede resolver, _is_ssrf debe bloquear (fail-closed)."""
    with patch("agentic_os.connectors.core.http.socket.getaddrinfo", side_effect=OSError("DNS failure")):
        assert HttpClient._is_ssrf("http://unresolvable.example.com/api"), \
            "SSRF no bloqueó ante fallo DNS (fail-closed violado)"
