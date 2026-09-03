from __future__ import annotations

import os
from typing import Any, Dict, Optional


class Config:
    """Configuración principal del sistema.

    Garantiza que no se expongan secretos en logs/pantalla mediante __repr__ y __str__ redactados,
    y falla de forma explícita si faltan variables de entorno obligatorias (sin fallback a llaves harcodeadas).
    """

    SECRET_FIELDS = {
        "api_key",
        "secret_key",
        "admin_key",
        "tenant_api_key",
        "database_url",
        "jwt_secret",
        "oauth_client_secret",
    }

    def __init__(self, env: Optional[Dict[str, str]] = None):
        source = env if env is not None else os.environ

        self.api_key: str = self._get_required_secret(source, "API_KEY")
        self.secret_key: str = self._get_required_secret(source, "SECRET_KEY")
        self.admin_key: Optional[str] = source.get("ADMIN_KEY")

        self.env: str = source.get("ENV", "production")
        self.debug: bool = source.get("DEBUG", "false").lower() in ("true", "1", "yes")

    @staticmethod
    def _get_required_secret(source: Dict[str, str], key: str) -> str:
        val = source.get(key)
        if not val or not val.strip():
            raise ValueError(
                f"Missing required secret environment variable: {key}. "
                "Fallback hardcoded keys are not allowed."
            )
        return val.strip()

    def to_dict(self, redact: bool = True) -> Dict[str, Any]:
        data = {
            "api_key": self.api_key,
            "secret_key": self.secret_key,
            "admin_key": self.admin_key,
            "env": self.env,
            "debug": self.debug,
        }
        if redact:
            for k in data:
                if k in self.SECRET_FIELDS and data[k] is not None:
                    data[k] = "***REDACTED***"
        return data

    def __repr__(self) -> str:
        redacted_data = self.to_dict(redact=True)
        items = ", ".join(f"{k}={v!r}" for k, v in redacted_data.items())
        return f"Config({items})"

    def __str__(self) -> str:
        return self.__repr__()
