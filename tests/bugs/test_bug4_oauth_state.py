"""Bug 4 - OAuth sin verificación de state + inyección URL: oauth_manager.py concatena query sin urlencode y no valida state"""

import pytest
from unittest.mock import patch, MagicMock
from agentic_os.connectors.auth.oauth_manager import OAuthManager


def test_authorization_url_uses_urlencode():
    """authorization_url debe codificar los parámetros correctamente (urlencode)."""
    from urllib.parse import urlparse, parse_qs
    config = {
        "client_id": "my-client-id",
        "redirect_uri": "http://localhost:8000/callback",
        "authorization_url": "https://accounts.google.com/o/oauth2/auth",
        "scopes": ["https://mail.google.com/", "https://www.googleapis.com/auth/calendar"],
        "access_type": "offline",
    }
    url = OAuthManager.authorization_url(config, state="test-state-123")
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    # Los scopes deben estar codificados (espacios como %20 o +)
    assert "scope" in params, "Falta parámetro scope en la URL"
    # El state debe aparecer correctamente
    assert "state" in params, "Falta parámetro state en la URL"
    assert params["state"] == ["test-state-123"], "State no coincide"


def test_authorization_url_encodes_special_chars():
    """Los caracteres especiales en redirect_uri deben codificarse."""
    from urllib.parse import urlparse, parse_qs
    config = {
        "client_id": "client_id",
        "redirect_uri": "http://localhost:8000/callback?foo=bar&baz=qux",
        "authorization_url": "https://example.com/auth",
        "scopes": ["scope1"],
    }
    url = OAuthManager.authorization_url(config)
    parsed = urlparse(url)
    # La redirect_uri debe estar codificada como valor del parámetro
    params = parse_qs(parsed.query)
    assert "redirect_uri" in params
    assert params["redirect_uri"] == ["http://localhost:8000/callback?foo=bar&baz=qux"]


def test_state_is_generated_if_not_provided():
    """Si no se proporciona state, se debe generar uno automáticamente."""
    config = {
        "client_id": "client_id",
        "redirect_uri": "http://localhost/callback",
        "authorization_url": "https://example.com/auth",
        "scopes": ["scope1"],
    }
    url = OAuthManager.authorization_url(config)
    from urllib.parse import urlparse, parse_qs
    params = parse_qs(urlparse(url).query)
    assert "state" in params, "No se generó state automático"
    assert len(params["state"][0]) > 0, "State generado está vacío"


def test_validate_state_rejects_mismatch():
    """validate_state debe rechazar un state que no coincida con el original."""
    # OAuthManager debería tener un método validate_state
    assert hasattr(OAuthManager, 'validate_state'), \
        "OAuthManager necesita un método validate_state para prevenir CSRF"
    # Si existe, debe rechazar states que no coincidan
    if hasattr(OAuthManager, 'validate_state'):
        assert not OAuthManager.validate_state("original", "different"), \
            "validate_state aceptó un state incorrecto"
        assert OAuthManager.validate_state("same", "same"), \
            "validate_state rechazó un state correcto"
