from __future__ import annotations

from typing import Callable, Optional
from fastapi import Depends, Header, HTTPException, status

from ...infrastructure.config.settings import Settings
from ...infrastructure.auth.models import AuthenticatedUser
from ...infrastructure.auth.google_workspace import (
    GoogleWorkspaceProvider,
    MockGoogleWorkspaceProvider,
    DomainRestrictionError,
    InvalidTokenError,
)
from ...kernel.policy.engine import PolicyEngine
from ...domains.clinic.policies import CLINIC_POLICY

# Shared policy engine instance (can be overridden via dependency injection)
_policy_engine = PolicyEngine(CLINIC_POLICY)
_workspace_provider: Optional[GoogleWorkspaceProvider] = None


def get_policy_engine() -> PolicyEngine:
    return _policy_engine


def set_policy_engine(engine: PolicyEngine) -> None:
    global _policy_engine
    _policy_engine = engine


def get_workspace_provider() -> GoogleWorkspaceProvider:
    global _workspace_provider
    if _workspace_provider is None:
        settings = Settings()
        if settings.auth_disabled or not settings.google_client_id:
            _workspace_provider = MockGoogleWorkspaceProvider()
        else:
            _workspace_provider = GoogleWorkspaceProvider()
    return _workspace_provider


def set_workspace_provider(provider: GoogleWorkspaceProvider) -> None:
    global _workspace_provider
    _workspace_provider = provider


def get_current_user(
    authorization: Optional[str] = Header(None),
    provider: GoogleWorkspaceProvider = Depends(get_workspace_provider),
) -> AuthenticatedUser:
    """Extracts and verifies Google ID token from Authorization header."""
    settings = Settings()
    if settings.auth_disabled:
        return AuthenticatedUser(
            id="dev-user-id",
            email="dev@example.com",
            name="Developer User",
            roles=["admin", "clinician", "operator", "user"],
        )

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header. Expected 'Bearer <token>'.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.split("Bearer ", 1)[1].strip()
    try:
        user = provider.verify_id_token(token)
        return user
    except DomainRestrictionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Google account domain restricted: {e}",
        )
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Google ID token: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication error: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_capability(capability: str) -> Callable[..., AuthenticatedUser]:
    """Dependency factory that validates whether the authenticated user's roles satisfy PolicyEngine."""

    def _dependency(
        user: AuthenticatedUser = Depends(get_current_user),
        policy_engine: PolicyEngine = Depends(get_policy_engine),
    ) -> AuthenticatedUser:
        decision = policy_engine.can(capability, None, user.roles)
        if decision.effect != "allow":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Policy denied capability '{capability}': {decision.reason or 'Insufficient permissions'}",
            )
        return user

    return _dependency


def get_log() -> None:
    return None


