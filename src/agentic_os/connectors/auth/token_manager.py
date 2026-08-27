from __future__ import annotations

from datetime import datetime, timezone

from ..core.config import CredentialSet


class TokenManager:
    """Gestión de expiración y refresh de tokens."""

    @staticmethod
    def is_expired(expires_at: datetime | None) -> bool:
        if not expires_at:
            return False
        return datetime.now(timezone.utc) >= expires_at.replace(tzinfo=timezone.utc)

    @staticmethod
    def refresh_if_needed(
        credential_set: CredentialSet,
        oauth_config: dict | None,
    ) -> CredentialSet:
        if credential_set.auth_type != "oauth2":
            return credential_set
        if not TokenManager.is_expired(credential_set.expires_at):
            return credential_set

        if oauth_config and credential_set.data.get("refresh_token"):
            from .oauth_manager import OAuthManager

            refreshed = OAuthManager.refresh(
                oauth_config, str(credential_set.data.get("refresh_token"))
            )
            if refreshed:
                credential_set.data["access_token"] = refreshed["access_token"]
                expires_in = refreshed.get("expires_in", 3600)
                from datetime import timedelta

                credential_set.expires_at = datetime.now(timezone.utc) + timedelta(
                    seconds=expires_in
                )
        return credential_set
