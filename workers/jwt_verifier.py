from __future__ import annotations
import time
from typing import Dict, Any, Optional
import jwt
from jwt import PyJWKClient
from pydantic import BaseModel
import os

class TenantClaims(BaseModel):
    tenant_id: str
    org_role: str = "member"
    client_id: Optional[str] = None
    user_id: str
    email: Optional[str] = None

class JWTVerifier:
    """Verifica JWT RS256 de Supabase contra su JWKS. Cache 1h. Nivel Enterprise."""
    def __init__(self, jwks_url: str):
        self.jwks_url = jwks_url
        self._jwk_client = PyJWKClient(jwks_url, cache_keys=True, lifespan=3600)

    def verify(self, token: str) -> TenantClaims:
        signing_key = self._jwk_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256", "ES256"],
            options={"verify_aud": False}
        )
        tenant_id = payload.get("tenant_id") or payload.get("user_metadata", {}).get("tenant_id")
        if not tenant_id:
            # Fallback para dev: si no hay hook aún, usa slug del header si existe
            raise ValueError("JWT sin tenant_id - activa custom_access_token_hook en Supabase")

        return TenantClaims(
            tenant_id=str(tenant_id),
            org_role=payload.get("org_role", "member"),
            client_id=payload.get("client_id"),
            user_id=payload.get("sub"),
            email=payload.get("email")
        )

_verifier: Optional[JWTVerifier] = None

def get_verifier() -> JWTVerifier:
    global _verifier
    if _verifier is None:
        supabase_url = os.getenv("SUPABASE_URL") or os.getenv("SUPABASE_PROJECT_URL")
        if not supabase_url:
            # intenta leer de settings
            try:
                from agentic_os.infrastructure.config.settings import settings
                supabase_url = settings.supabase_url
            except Exception:
                raise RuntimeError("SUPABASE_URL no configurado para verificar JWT")
        jwks = f"{supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
        _verifier = JWTVerifier(jwks)
    return _verifier
