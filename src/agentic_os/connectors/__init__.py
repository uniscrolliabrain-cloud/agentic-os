"""Connector Kernel: capa de ejecución/conectividad del sistema.

Límite cerrado entre miniagentes y el mundo real. Los agentes nunca reciben
credenciales, clientes SDK, HTTP clients ni endpoints: solo reciben Command
(pydantic) y devuelven CommandResult (pydantic).

Estructura:
  core/    interfaces, modelos, HTTP, retry, rate-limiter, auditoría
  auth/    CredentialStore, OAuthManager, TokenManager, CredentialResolver
  registry/ CapabilityRegistry
  router/   ConnectorRouter (selección determinista de connector)
  factory/  ConnectorFactory
  providers/ adaptadores por proveedor (Google, Microsoft, HubSpot...)
  webhook/  recepción y validación de webhooks
"""

from .core.base import Connector
from .core.config import ConnectorConfig, CredentialSet, RetryPolicy, RateLimitPolicy
from .core.http import HttpClient
from .core.rate_limiter import RateLimiter
from .core.retry import RetryEngine
from .core.audit import AuditLog
from .core.telemetry import EventRecorder
from .auth.credential_store import CredentialStore, EncodedFileCredentialStore
from .auth.token_manager import TokenManager
from .auth.oauth_manager import OAuthManager
from .auth.credential_resolver import CredentialResolver
from .registry import CapabilityRegistry
from .factory import ConnectorFactory
from .router import ConnectorRouter

__all__ = [
    "Connector",
    "ConnectorConfig",
    "CredentialSet",
    "RetryPolicy",
    "RateLimitPolicy",
    "HttpClient",
    "RateLimiter",
    "RetryEngine",
    "AuditLog",
    "EventRecorder",
    "CredentialStore",
    "EncodedFileCredentialStore",
    "TokenManager",
    "OAuthManager",
    "CredentialResolver",
    "CapabilityRegistry",
    "ConnectorFactory",
    "ConnectorRouter",
]
