from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class AuthenticatedUser(BaseModel):
    """Pydantic model representing an authenticated user via Google OAuth."""
    model_config = ConfigDict(frozen=True)

    id: str = Field(..., description="Google subject user ID (sub)")
    email: str = Field(..., description="User's email address")
    name: str = Field(default="", description="Display name of the user")
    picture: Optional[str] = Field(default=None, description="Profile picture URL")
    domain: Optional[str] = Field(default=None, description="Hosted Google Workspace domain (hd)")
    roles: List[str] = Field(default_factory=list, description="Assigned roles within Agentic OS")
    scopes: List[str] = Field(default_factory=list, description="Granted OAuth scopes")

    def has_role(self, role: str) -> bool:
        return role in self.roles or "admin" in self.roles


class WorkspaceCredentials(BaseModel):
    """Pydantic model representing Google Workspace OAuth credentials."""
    model_config = ConfigDict(frozen=True)

    access_token: str = Field(..., description="OAuth 2.0 access token")
    refresh_token: Optional[str] = Field(default=None, description="OAuth 2.0 refresh token")
    token_uri: str = Field(default="https://oauth2.googleapis.com/token", description="Token endpoint")
    client_id: Optional[str] = Field(default=None, description="OAuth client ID")
    client_secret: Optional[str] = Field(default=None, description="OAuth client secret")
    scopes: List[str] = Field(default_factory=list, description="Granted scopes")
    expiry: Optional[datetime] = Field(default=None, description="Token expiration timestamp")


class OAuthCallbackParams(BaseModel):
    """Pydantic model for OAuth authorization code callback."""
    code: str = Field(..., description="Authorization code returned by Google OAuth")
    state: Optional[str] = Field(default=None, description="State param for CSRF protection")
