from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from ..core.errors import AuthenticationError


class OAuthManager:
    """Gestión de OAuth2: authorization URL, code exchange, refresh, revoke.

    Configurable vía los valores de client_id/secret/token_url declarados en
    el manifest del provider. Ninguna credencial real está en el código.
    """

    @staticmethod
    def authorization_url(oauth_config: Dict[str, Any], state: Optional[str] = None) -> str:
        state = state or uuid.uuid4().hex
        _ = state
        params = {
            "client_id": oauth_config["client_id"],
            "redirect_uri": oauth_config["redirect_uri"],
            "response_type": "code",
            "scope": " ".join(oauth_config.get("scopes", [])),
            "state": state,
            "access_type": oauth_config.get("access_type", "offline"),
        }
        qs = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{oauth_config['authorization_url']}?{qs}"

    @staticmethod
    def exchange_code(oauth_config: Dict[str, Any], code: str) -> Optional[Dict[str, Any]]:
        import httpx

        data = {
            "client_id": oauth_config["client_id"],
            "client_secret": oauth_config["client_secret"],
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": oauth_config["redirect_uri"],
        }
        try:
            resp = httpx.post(oauth_config["token_url"], data=data, timeout=15)
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return None

    @staticmethod
    def refresh(oauth_config: Dict[str, Any], refresh_token: str) -> Optional[Dict[str, Any]]:
        import httpx

        data = {
            "client_id": oauth_config["client_id"],
            "client_secret": oauth_config.get("client_secret", ""),
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }
        try:
            resp = httpx.post(oauth_config["token_url"], data=data, timeout=15)
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return None

    @staticmethod
    def revoke(oauth_config: Dict[str, Any], token: str) -> bool:
        revoke_url = oauth_config.get("revocation_url")
        if not revoke_url:
            return False
        import httpx

        try:
            resp = httpx.post(
                revoke_url,
                data={"token": token, "token_type_hint": "access_token"},
                timeout=10,
            )
            return resp.status_code in (200, 204)
        except Exception:
            return False

    @staticmethod
    def build_authorization_url(oauth_config: Dict[str, Any]) -> str:
        return OAuthManager.authorization_url(oauth_config)
