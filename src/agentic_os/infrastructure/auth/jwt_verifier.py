from __future__ import annotations
import time
import os
from typing import Dict, Any, Optional
import jwt
from jwt import PyJWKClient
from pydantic import BaseModel

class TenantClaims(BaseModel):
    tenant_id: str
    org_role: str = "member"
    client_id: Optional[str] = None
    user_id: str
    email: Optional[str] = None

class JWTVerifier:
    """Verifica JWT RS256 de Supabase contra su JWKS. Cache 1h."""
    def __init__(self, jwks_url: str):
        self.jwks_url = jwks_url
        self._jwk_client = PyJWKClient(
            jwks_url, cache_keys=True, lifespan=3600, timeout=10,
        )

    def verify(self, token: str) -> TenantClaims:
        signing_key = self._jwk_client.get_signing_key_from_jwt(token)
        key_obj = signing_key.key
        key_type = getattr(key_obj, "key_type", None)
        if key_type == "RSA":
            algorithms = ["RS256"]
        elif key_type in ("EC", "OKP"):
            algorithms = ["ES256"]
        else:
            algorithms = ["RS256"]
        options = {"verify_aud": True}
        decode_kwargs: Dict[str, Any] = {
            "algorithms": algorithms, "options": options,
        }
        audience = os.getenv("SUPABASE_JWT_AUD")
        if audience:
            decode_kwargs["audience"] = audience
        payload = jwt.decode(token, key_obj, **decode_kwargs)
        user_metadata = payload.get("user_metadata")
        if isinstance(user_metadata, dict):
            tenant_id = payload.get("tenant_id") or user_metadata.get("tenant_id")
        else:
            tenant_id = payload.get("tenant_id")
        if not tenant_id:
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
        supabase_url = os.getenv("SUPABASE_URL", "").strip() or os.getenv("SUPABASE_PROJECT_URL", "").strip()
        if not supabase_url:
            try:
                from agentic_os.infrastructure.config.settings import settings
                supabase_url = settings.supabase_url or settings.supabase_project_url
            except Exception:
                raise RuntimeError("SUPABASE_URL no configurado para verificar JWT")
        if not supabase_url:
            raise RuntimeError("SUPABASE_URL no configurado para verificar JWT")
        jwks = f"{supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
        _verifier = JWTVerifier(jwks)
    return _verifier
