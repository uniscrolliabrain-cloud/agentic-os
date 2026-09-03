from __future__ import annotations

import base64
import json
import logging
from pathlib import Path
from typing import Any, Dict

from ..core.config import CredentialSet

logger = logging.getLogger(__name__)


def _secret_value(value: Any) -> str:
    """Desenvuelve pydantic Secret/SecretStr; str() plano para lo demás.

    str(Secret) devuelve la máscara '**********', NUNCA el valor real:
    usar str() directamente destruiría las credenciales al guardarlas.
    """
    getter = getattr(value, "get_secret_value", None)
    if callable(getter):
        return str(getter())
    return str(value)



def _cred_path(workspace: str, provider: str, base: Path | None = None) -> Path:
    """Resuelve la ruta del fichero de credenciales.

    Usa SIEMPRE el `base` de la instancia CredentialStore cuando se aporta,
    para que un CredentialStore(cred_dir=...) no ignore su propio directorio
    releyendo la variable de entorno.
    """
    if base is not None:
        return Path(base) / workspace / f"{provider}.json"
    import os

    fallback = os.environ.get("CONNECTOR_CRED_DIR") or ".credentials"
    return Path(fallback) / workspace / f"{provider}.json"


class EncodedFileCredentialStore:
    """Codificación base64 de credenciales en disco — NO es encriptación.

    ⚠️ ADVERTENCIA: base64 NO protege las credenciales. Cualquiera con acceso
    al fichero puede decodificarlo. Esto es SOLO un almacenamiento transitorio
    para desarrollo.

    TODO(security): para producción reemplazar por un secret manager real
    (HashiCorp Vault, AWS KMS, GCP Secret Manager) con rotación y auditoría.
    """

    # TODO(security): migrar a Vault/KMS antes de conectar providers reales.

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
        # Mejor esfuerzo (Unix): restrictivo, no world-readable.
        try:
            self.cred_dir.chmod(0o700)
        except OSError:
            pass

        # Advertencia si el directorio de credenciales vive dentro del repo:
        # riesgo de commit accidental y acceso por el código.
        repo_root = Path(__file__).resolve().parents[4]
        try:
            self.cred_dir.resolve().relative_to(repo_root.resolve())
            logger.warning(
                "CONNECTOR_CRED_DIR (%s) está dentro del repositorio. "
                "Conecta un secret manager o usa un directorio fuera del código.",
                self.cred_dir,
            )
        except ValueError:
            pass

    def save(self, workspace: str, provider: str, credential_set: CredentialSet) -> None:
        path = _cred_path(workspace, provider, self.cred_dir)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "provider": provider,
            "auth_type": credential_set.auth_type,
            "data": {k: EncodedFileCredentialStore.encrypt(_secret_value(v)) for k, v in credential_set.data.items()},
            "expires_at": credential_set.expires_at.isoformat() if credential_set.expires_at else None,
            "scopes": credential_set.scopes,
        }
        with open(path, "w") as f:
            json.dump(data, f)
        # Mejor esfuerzo (Unix): el fichero no debe ser legible por otros usuarios.
        try:
            path.chmod(0o600)
        except OSError:
            pass

    def load(self, workspace: str, provider: str) -> "CredentialSet | None":
        path = _cred_path(workspace, provider, self.cred_dir)
        if not path.exists():
            return None
        with open(path) as f:
            data = json.load(f)
        cred_data = {k: EncodedFileCredentialStore.decrypt(v) for k, v in data.get("data", {}).items()}
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
        path = _cred_path(workspace, provider, self.cred_dir)
        if path.exists():
            path.unlink()
            return True
        return False
