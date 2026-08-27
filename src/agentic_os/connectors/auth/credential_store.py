from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Dict

from ..core.config import CredentialSet


def _cred_path(workspace: str, provider: str) -> Path:
    import os

    base = os.environ.get("CONNECTOR_CRED_DIR") or ".credentials"
    return Path(base) / workspace / f"{provider}.json"


class EncryptedStore:
    """Almacenamiento básico de credenciales en disco (codificado base64).

    Para producción, reemplazar con encriptación real (Vault, AWS KMS, etc).
    """

    @staticmethod
    def encrypt(value: str) -> str:
        return base64.b64encode(value.encode()).decode()

    @staticmethod
    def decrypt(value: str) -> str:
        try:
            return base64.b64decode(value.encode()).decode()
        except Exception:
            return ""


class CredentialStore:
    """Gestor de credenciales por workspace + provider.

    Las credenciales reales se cargan desde archivos .env o secretos;
    este código solo provee la estructura para almacenarlas de forma segura.
    Nunca se hardcodean valores reales.
    """

    def __init__(self, cred_dir: str = None):
        import os

        self.cred_dir = Path(cred_dir or os.environ.get("CONNECTOR_CRED_DIR") or ".credentials")
        self.cred_dir.mkdir(parents=True, exist_ok=True)

    def save(self, workspace: str, provider: str, credential_set: CredentialSet) -> None:
        path = _cred_path(workspace, provider)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "provider": provider,
            "auth_type": credential_set.auth_type,
            "data": {k: EncryptedStore.encrypt(str(v)) for k, v in credential_set.data.items()},
            "expires_at": credential_set.expires_at.isoformat() if credential_set.expires_at else None,
            "scopes": credential_set.scopes,
        }
        with open(path, "w") as f:
            json.dump(data, f)

    def load(self, workspace: str, provider: str) -> "CredentialSet | None":
        path = _cred_path(workspace, provider)
        if not path.exists():
            return None
        with open(path) as f:
            data = json.load(f)
        cred_data = {k: EncryptedStore.decrypt(v) for k, v in data.get("data", {}).items()}
        expires = None
        if data.get("expires_at"):
            try:
                from datetime import datetime

                expires = datetime.fromisoformat(data["expires_at"])
            except ValueError:
                pass
        return CredentialSet(
            provider=data["provider"],
            auth_type=data["auth_type"],
            data=cred_data,
            expires_at=expires,
            scopes=data.get("scopes", []),
        )

    def delete(self, workspace: str, provider: str) -> bool:
        path = _cred_path(workspace, provider)
        if path.exists():
            path.unlink()
            return True
        return False
