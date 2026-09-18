"""AuthStub (BUILD_PLAN 0b). Auth single-user sin JWT.

Cuando ENABLE_JWT=false, todo se resuelve a un usuario local unico.
Objetivo: desarrollo y vertical slice sin montar auth completo.

El codigo del orquestador no sabe si JWT esta on u off. Solo pide
"quien es el usuario actual" y recibe un user_id.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict


class LocalUser(BaseModel):
    """Usuario unico para modo single-user."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    user_id: str = "local-user"
    tenant_id: Optional[str] = None
    role: str = "director"


class AuthStub:
    """Auth single-user. Devuelve siempre el mismo LocalUser."""

    def current_user(self) -> LocalUser:
        return LocalUser()

    def user_id(self) -> str:
        return "local-user"

    def role(self) -> str:
        return "director"


_stub_singleton: Optional[AuthStub] = None


def get_auth() -> AuthStub:
    """Devuelve el auth activo. Por ahora siempre stub.

    Cuando se active JWT real (ENABLE_JWT=true), esta funcion devuelve
    un auth basado en JWT. El contrato (current_user, user_id, role)
    es el mismo.
    """
    global _stub_singleton
    if _stub_singleton is None:
        _stub_singleton = AuthStub()
    return _stub_singleton


__all__ = ["LocalUser", "AuthStub", "get_auth"]

