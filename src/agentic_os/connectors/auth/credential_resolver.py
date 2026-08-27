from __future__ import annotations

import base64
from typing import Dict

from ..core.config import CredentialSet
from ..core.errors import AuthenticationError


class CredentialResolver:
    """Construye los headers de autenticación a partir del CredentialSet."""

    @staticmethod
    def build_headers(
        auth_type: str, credential_set: CredentialSet
    ) -> Dict[str, str]:
        if auth_type == "bearer":
            token = credential_set.data.get("access_token") or credential_set.data.get("token")
            if not token:
                raise AuthenticationError("No se encontró el token bearer")
            return {"Authorization": f"Bearer {token}"}
        if auth_type == "api_key":
            key_name = credential_set.data.get("key_name", "X-API-Key")
            key_value = credential_set.data.get("api_key")
            if not key_value:
                raise AuthenticationError("No se encontró la API key")
            return {key_name: key_value}
        if auth_type == "basic":
            user = credential_set.data.get("username", "")
            pwd = credential_set.data.get("password", "")
            if not user or not pwd:
                raise AuthenticationError("Credenciales básicas incompletas")
            b64 = base64.b64encode(f"{user}:{pwd}".encode()).decode()
            return {"Authorization": f"Basic {b64}"}
        if auth_type == "custom_header":
            header_name = credential_set.data.get("header_name", "Authorization")
            header_value = credential_set.data.get("header_value", "")
            if not header_value:
                raise AuthenticationError("Header personalizado sin valor")
            return {header_name: header_value}
        return {}

    @staticmethod
    def validate(credential_set: CredentialSet) -> bool:
        if not credential_set.valid:
            return False
        from .token_manager import TokenManager

        if credential_set.auth_type == "oauth2" and TokenManager.is_expired(
            credential_set.expires_at
        ):
            if not credential_set.data.get("refresh_token"):
                return False
        return True
