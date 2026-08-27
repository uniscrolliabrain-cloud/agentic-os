"""core: interfaces y modelos base del Connector Kernel."""

from .base import Connector, ProviderAdapter
from .models import (
    Artifact,
    Command,
    CommandResult,
    CredentialStatus,
    HealthStatus,
    Page,
    RiskClass,
    canonical_models,
)
from .errors import (
    AuthenticationError,
    AuthorizationError,
    ConnectorError,
    ConnectorUnavailable,
    CredentialError,
    NormalizedError,
)
from .config import ConnectorConfig, CredentialSet, RetryPolicy, RateLimitPolicy, ProviderManifest
from .http import HttpClient
from .rate_limiter import RateLimiter
from .retry import RetryEngine
from .audit import AuditLog
from .telemetry import EventRecorder, TelemetryEvent

__all__ = [
    "Connector",
    "ProviderAdapter",
    "Command",
    "CommandResult",
    "CredentialStatus",
    "HealthStatus",
    "Page",
    "Artifact",
    "RiskClass",
    "canonical_models",
    "NormalizedError",
    "ConnectorError",
    "AuthenticationError",
    "AuthorizationError",
    "CredentialError",
    "ConnectorUnavailable",
    "ConnectorConfig",
    "CredentialSet",
    "RetryPolicy",
    "RateLimitPolicy",
    "ProviderManifest",
    "HttpClient",
    "RateLimiter",
    "RetryEngine",
    "AuditLog",
    "EventRecorder",
    "TelemetryEvent",
]