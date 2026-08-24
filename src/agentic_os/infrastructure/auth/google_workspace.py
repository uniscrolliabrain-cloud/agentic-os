from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple
from google.oauth2.credentials import Credentials
from google.oauth2 import id_token
import google.auth.transport.requests

from ..config.settings import Settings
from .models import AuthenticatedUser, WorkspaceCredentials

logger = logging.getLogger(__name__)


class DomainRestrictionError(Exception):
    """Raised when an authenticated Google user is not in the allowed domains."""
    pass


class InvalidTokenError(Exception):
    """Raised when an OAuth token is invalid or expired."""
    pass


class GoogleWorkspaceProvider:
    """Provider for Google OAuth authentication and Google Workspace API services."""

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        allowed_domains: Optional[List[str]] = None,
        scopes: Optional[List[str]] = None,
    ):
        settings = Settings()
        self.client_id = client_id or settings.google_client_id
        self.client_secret = client_secret or settings.google_client_secret
        self.allowed_domains = (
            allowed_domains if allowed_domains is not None else settings.google_allowed_domains
        )
        self.scopes = scopes if scopes is not None else settings.google_workspace_scopes

    def verify_id_token(self, token_str: str) -> AuthenticatedUser:
        """Verifies a Google ID token and returns an AuthenticatedUser."""
        request = google.auth.transport.requests.Request()
        try:
            payload = id_token.verify_oauth2_token(  # type: ignore[no-untyped-call]
                token_str, request, audience=self.client_id
            )
        except Exception as e:
            raise InvalidTokenError(f"Google ID token verification failed: {e}") from e

        domain = payload.get("hd")
        if self.allowed_domains and domain not in self.allowed_domains:
            raise DomainRestrictionError(
                f"Domain '{domain}' is not in allowed domains: {self.allowed_domains}"
            )

        roles = self._resolve_roles(payload)

        return AuthenticatedUser(
            id=str(payload.get("sub")),
            email=str(payload.get("email")),
            name=str(payload.get("name", "")),
            picture=payload.get("picture"),
            domain=domain,
            roles=roles,
            scopes=self.scopes,
        )

    def _resolve_roles(self, payload: Dict[str, Any]) -> List[str]:
        """Resolves system roles based on user email, domain or claims."""
        roles: List[str] = ["user"]
        email = payload.get("email", "")
        if email.startswith("admin@") or email.startswith("doctor@") or email.startswith("clinician@"):
            roles.append("clinician")
            roles.append("operator")
        if email.startswith("admin@"):
            roles.append("admin")
        return roles

    def build_credentials(self, workspace_creds: WorkspaceCredentials) -> Credentials:
        """Constructs a google.oauth2.credentials.Credentials instance."""
        return Credentials(  # type: ignore[no-untyped-call]
            token=workspace_creds.access_token,
            refresh_token=workspace_creds.refresh_token,
            token_uri=workspace_creds.token_uri,
            client_id=workspace_creds.client_id or self.client_id,
            client_secret=workspace_creds.client_secret or self.client_secret,
            scopes=workspace_creds.scopes or self.scopes,
        )


class MockGoogleWorkspaceProvider(GoogleWorkspaceProvider):
    """Deterministic mock provider for offline development, testing, and CI."""

    def __init__(
        self,
        mock_user: Optional[AuthenticatedUser] = None,
        allowed_domains: Optional[List[str]] = None,
    ):
        super().__init__(allowed_domains=allowed_domains)
        self.mock_user = mock_user or AuthenticatedUser(
            id="mock-google-sub-12345",
            email="clinician@healthcorp.com",
            name="Dr. Jane Doe",
            domain="healthcorp.com",
            roles=["user", "clinician", "operator"],
            scopes=["https://www.googleapis.com/auth/gmail.send", "https://www.googleapis.com/auth/calendar.events"],
        )

    def verify_id_token(self, token_str: str) -> AuthenticatedUser:
        if token_str == "invalid_token":
            raise InvalidTokenError("Invalid mock token")
        if token_str == "unauthorized_domain_token":
            if self.allowed_domains:
                raise DomainRestrictionError("Domain not allowed in mock")
        return self.mock_user
