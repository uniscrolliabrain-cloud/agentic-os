"""Errores normalizados. Nunca se filtran errores crudos del provider a los agentes."""

from __future__ import annotations

from typing import Optional


class NormalizedError:
    """Taxonomía canónica de errores del connector layer."""

    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    AUTHORIZATION_ERROR = "AUTHORIZATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    RATE_LIMIT_ERROR = "RATE_LIMIT_ERROR"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"
    NETWORK_ERROR = "NETWORK_ERROR"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    CONFLICT_ERROR = "CONFLICT_ERROR"
    DUPLICATE_ERROR = "DUPLICATE_ERROR"
    UNSUPPORTED_OPERATION = "UNSUPPORTED_OPERATION"
    CREDENTIAL_ERROR = "CREDENTIAL_ERROR"
    CONNECTOR_NOT_CONFIGURED = "CONNECTOR_NOT_CONFIGURED"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


class ConnectorError(Exception):
    """Base de todos los errores normalizados del connector layer."""

    error_type: str = NormalizedError.UNKNOWN_ERROR

    def __init__(
        self,
        message: str = "",
        *,
        provider: Optional[str] = None,
        capability: Optional[str] = None,
        retryable: bool = False,
        code: Optional[int] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.provider = provider
        self.capability = capability
        self.retryable = retryable
        self.code = code


class AuthenticationError(ConnectorError):
    error_type = NormalizedError.AUTHENTICATION_ERROR


class AuthorizationError(ConnectorError):
    error_type = NormalizedError.AUTHORIZATION_ERROR


class NotFoundError(ConnectorError):
    error_type = NormalizedError.NOT_FOUND


class ValidationError(ConnectorError):
    error_type = NormalizedError.VALIDATION_ERROR


class RateLimitError(ConnectorError):
    error_type = NormalizedError.RATE_LIMIT_ERROR

    def __init__(self, message="", *, provider=None, capability=None, retryable=True, retry_after=None, code=None):
        super().__init__(message, provider=provider, capability=capability, retryable=retryable, code=code)
        self.retry_after = retry_after


class TimeoutError_(ConnectorError):
    error_type = NormalizedError.TIMEOUT_ERROR


class NetworkError(ConnectorError):
    error_type = NormalizedError.NETWORK_ERROR


class ProviderError(ConnectorError):
    error_type = NormalizedError.PROVIDER_ERROR


class ConflictError(ConnectorError):
    error_type = NormalizedError.CONFLICT_ERROR


class DuplicateError(ConnectorError):
    error_type = NormalizedError.DUPLICATE_ERROR


class UnsupportedOperationError(ConnectorError):
    error_type = NormalizedError.UNSUPPORTED_OPERATION


class CredentialError(ConnectorError):
    error_type = NormalizedError.CREDENTIAL_ERROR


class ConnectorUnavailable(ConnectorError):
    """El connector no está conectado/configurado todavía (los providers se crean
    sin conectar a las APIs destino hasta que se provean credenciales reales)."""

    error_type = NormalizedError.CONNECTOR_NOT_CONFIGURED


def normalize_exception(exc: Exception) -> ConnectorError:
    """Convierte una excepción cruda en un ConnectorError normalizado (si no lo es)."""
    if isinstance(exc, ConnectorError):
        return exc
    msg = str(exc) or exc.__class__.__name__
    return ConnectorError(msg)