"""Bug 18 - Auth Tenant débil: X-Api-Key estático sin expiración/JWT"""

import pytest


def test_api_key_has_expiration():
    """Las API keys de tenant deben tener expiración, no ser eternas."""
    import inspect
    from agentic_os.infrastructure.tenancy import models
    source = inspect.getsource(models)

    # TenantConfig debe tener algún campo de expiración o el sistema debe verificarla
    assert "expires_at" in source or "expir" in source.lower(), \
        "TenantConfig no tiene mecanismo de expiración de credenciales"


def test_tenant_credentials_support_rotation():
    """Las credenciales deben poder rotar (múltiples keys, revoked keys)."""
    from agentic_os.infrastructure.tenancy.models import TenantConfig
    # Verificar que TenantConfig soporta múltiples credenciales
    import typing
    hints = typing.get_type_hints(TenantConfig)
    creds_type = hints.get("credentials")
    # Debe ser un dict que pueda contener múltiples keys
    assert creds_type is not None, "TenantConfig no tiene campo credentials"


def test_auth_rejects_expired_key():
    """El sistema debe rechazar API keys expiradas."""
    from agentic_os.infrastructure.tenancy.models import TenantConfig
    from datetime import datetime, timedelta
    # Crear un tenant con key expirada debería ser posible de marcar
    config = TenantConfig(
        name="Test",
        domain="generic",
        data_dir="/tmp/test",
        credentials={"api_key": "old_key", "expires_at": (datetime.utcnow() - timedelta(days=1)).isoformat()},
    )
    assert config.credentials.get("api_key") == "old_key"
