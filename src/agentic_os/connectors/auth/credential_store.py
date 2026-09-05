from __future__ import annotations

import base64
import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from ..core.config import CredentialSet

logger = logging.getLogger(__name__)

# Clave Fernet usada durante la sesión cuando no hay CREDENTIAL_ENCRYPTION_KEY.
# Se genera una vez por proceso: permite cifrar/descifrar en runtime pero NO
# persiste las credenciales entre reinicios sin clave configurada.
_module_fernet = None


def _fernet() -> "Fernet":
    """Devuelve una instancia Fernet estable para el proceso.

    Fuentes de clave, en orden de preferencia:
      1. settings.credential_encryption_key  (CREDENTIAL_ENCRYPTION_KEY)
      2. os.environ CREDENTIAL_ENCRYPTION_KEY
      3. clave aleatoria por proceso (solo dev; advertimos en logs)

    Si la clave dada no es una clave Fernet válida (32 bytes base64 u-safe),
    se deriva una estable vía SHA-256 para que valores legibles sirvan.
    """
    global _module_fernet
    if _module_fernet is not None:
        return _module_fernet

    from cryptography.fernet import Fernet

    raw_key: Optional[str] = None
    try:
        from ...infrastructure.config.settings import settings
        raw_key = getattr(settings, "credential_encryption_key", None)
    except Exception:
        raw_key = None
    if not raw_key:
        import os
        raw_key = os.environ.get("CREDENTIAL_ENCRYPTION_KEY")

    if raw_key:
        try:
            _module_fernet = Fernet(raw_key.encode())
            return _module_fernet
        except Exception:
            digest = hashlib.sha256(raw_key.encode()).digest()
            _module_fernet = Fernet(base64.urlsafe_b64encode(digest))
            return _module_fernet

    _module_fernet = Fernet(Fernet.generate_key())
    logger.warning(
        "CREDENTIAL_ENCRYPTION_KEY no configurada: usando clave cifrado por proceso. "
        "Las credenciales NO descifrarán tras un reinicio. Configúrala en .env para producción."
    )
    return _module_fernet


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
    """Resuelve la ruta del fichero de credenciales."""
    if base is not None:
        return Path(base) / workspace / f"{provider}.json"
    import os
    fallback = os.environ.get("CONNECTOR_CRED_DIR") or ".credentials"
    return Path(fallback) / workspace / f"{provider}.json"


class EncodedFileCredentialStore:
    """Credenciales cifradas en disco con Fernet (AES-128-CBC + HMAC).

    ⚠️ CREDENTIAL_ENCRYPTION_KEY es obligatoria para persistencia real entre
    reinicios. Sin ella se usa una clave por proceso (válida solo en runtime).

    Descifra de forma retrocompatible el formato base64 antiguo.
    """

    @staticmethod
    def encrypt(value: str) -> str:
        if not value:
            return value
        return _fernet().encrypt(value.encode()).decode()

    @staticmethod
    def decrypt(value: str) -> str:
        if not value:
            return ""
        # 1) Intentar descifrado Fernet (formato actual)
        try:
            return _fernet().decrypt(value.encode()).decode()
        except Exception:
            pass
        # 2) Retrocompatibilidad: el fichero puede venir de la versión base64.
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
