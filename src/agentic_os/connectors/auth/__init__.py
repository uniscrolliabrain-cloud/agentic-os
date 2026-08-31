"""Sistema de autenticación centralizada.

Las credenciales viven en el CredentialStore, resuelven por
workspace/connection/provider y se refrescan automáticamente.
Implementa API_KEY, BEARER, BASIC, OAUTH2, JWT y custom_header.

La infraestructura está preparada para recibir credenciales reales vía
.env/secretos. El código nunca contiene valores reales.
"""

from __future__ import annotations

from .credential_store import CredentialStore, EncodedFileCredentialStore
from .token_manager import TokenManager
from .oauth_manager import OAuthManager
from .credential_resolver import CredentialResolver

__all__ = [
    "CredentialStore",
    "EncodedFileCredentialStore",
    "TokenManager",
    "OAuthManager",
    "CredentialResolver",
]
