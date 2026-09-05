from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, Secret

from ...kernel.types.time import now_utc

from ...infrastructure.config.settings import Settings


class RetryPolicy(BaseModel):
    max_attempts: int = 3
    base_delay_s: float = 1.0
    max_delay_s: float = 30.0
    backoff_multiplier: float = 2.0
    jitter: bool = True
    retry_on: List[int] = [429, 500, 502, 503, 504]


class RateLimitPolicy(BaseModel):
    requests_per_minute: Optional[int] = None
    requests_per_second: Optional[int] = None
    daily_quota: Optional[int] = None
    burst_size: int = 1


class ConnectorConfig(BaseModel):
    connector_id: str
    provider: str
    version: str = "0.0.0"
    auth_type: str = "none"
    enabled: bool = True
    timeout_s: float = 30.0
    retry: RetryPolicy = Field(default_factory=RetryPolicy)
    rate_limit: RateLimitPolicy = Field(default_factory=RateLimitPolicy)
    dry_run_default: bool = True
    capabilities: List[str] = Field(default_factory=list)
    extra: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_manifest(cls, manifest: Dict[str, Any]) -> "ConnectorConfig":
        return cls(**manifest)


class CredentialSet(BaseModel):
    provider: str
    auth_type: str
    data: Dict[str, Secret[Any]] = Field(default_factory=dict)
    expires_at: Optional[datetime] = None
    scopes: List[str] = Field(default_factory=list)
    valid: bool = True

    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        # now_utc() es timezone-aware; normaliza expires_at naive→UTC
        expires = self.expires_at
        if expires.tzinfo is None:
            from datetime import timezone
            expires = expires.replace(tzinfo=timezone.utc)
        return now_utc() >= expires


class ProviderManifest(BaseModel):
    connector_id: str
    provider: str
    version: str
    capabilities: List[str]
    authentication: Dict[str, Any]
    health_check: Dict[str, Any]
    rate_limit: Dict[str, Any]
    oauth: Optional[Dict[str, Any]] = None


def load_settings() -> Settings:
    return Settings()
