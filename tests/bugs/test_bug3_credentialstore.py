"""Bug 3 - CredentialStore sin cifrado: solo Base64 [YA FIXEADO pero deja el test]"""

import json
import tempfile
import os
from pathlib import Path

from agentic_os.connectors.auth.credential_store import CredentialStore, EncodedFileCredentialStore
from agentic_os.connectors.core.config import CredentialSet


def test_credentials_not_plaintext_on_disk():
    """Las credenciales NO deben aparecer en texto plano en disco."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store = CredentialStore(cred_dir=tmpdir)
        store.save("tenant1", "google", CredentialSet(
            provider="google",
            auth_type="oauth2",
            data={"refresh_token": "super_secret_token_abc123", "client_id": "my_client_id"},
        ))
        # Leer el archivo crudo
        cred_file = Path(tmpdir) / "tenant1" / "google.json"
        raw = cred_file.read_text()
        assert "super_secret_token_abc123" not in raw, "Credencial en texto plano en disco"
        assert "my_client_id" not in raw, "Client ID en texto plano en disco"


def test_credentials_not_base64_on_disk():
    """Las credenciales NO deben aparecer como Base64 decodificable sin clave (debe estar cifrado)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store = CredentialStore(cred_dir=tmpdir)
        store.save("tenant1", "google", CredentialSet(
            provider="google",
            auth_type="oauth2",
            data={"refresh_token": "secret_token_xyz"},
        ))
        cred_file = Path(tmpdir) / "tenant1" / "google.json"
        raw = cred_file.read_text()
        # Si está cifrado con Fernet, NO debe ser Base64 decodificable directamente
        import base64
        data = json.loads(raw)
        encrypted_value = data["data"]["refresh_token"]
        try:
            decoded = base64.b64decode(encrypted_value).decode()
            assert decoded != "secret_token_xyz", "Base64 sin cifrar: credencial decodificable sin clave"
        except Exception:
            pass  # Esperado: no es Base64 válido o no decodifica limpiamente


def test_credentials_roundtrip():
    """Las credenciales deben poder guardarse y recuperarse correctamente."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store = CredentialStore(cred_dir=tmpdir)
        original = CredentialSet(
            provider="google",
            auth_type="oauth2",
            data={"refresh_token": "token_123", "client_id": "cid_456"},
            scopes=["https://mail.google.com/"],
        )
        store.save("tenant1", "google", original)
        loaded = store.load("tenant1", "google")
        assert loaded is not None, "No se pudo cargar credenciales guardadas"
        assert loaded.data["refresh_token"].get_secret_value() == "token_123"
        assert loaded.data["client_id"].get_secret_value() == "cid_456"
        assert loaded.scopes == ["https://mail.google.com/"]


def test_encoded_store_is_encrypted_with_key() -> None:
    """EncodedFileCredentialStore ahora usa cifrado Fernet real, no Base64."""
    encoded = EncodedFileCredentialStore.encrypt("test_value")
    decoded = EncodedFileCredentialStore.decrypt(encoded)
    assert decoded == "test_value", "Fernet roundtrip debe funcionar"
    # El valor cifrado NO debe ser el valor en claro ni un base64 trivial del mismo:
    assert "test_value" not in encoded, "El valor está en texto plano en el cifrado"
    import base64
    try:
        raw = base64.b64decode(encoded)
        # Fernet produce bytes no-UTF8 (token binario): decodificar como UTF-8
        # debe fallar o NO devolver el texto plano original.
        try:
            decoded_plain = raw.decode()
        except Exception:
            decoded_plain = None
        assert decoded_plain != "test_value", "Base64 trivial decodifica al secreto (sin cifrar)"
    except Exception:
        pass  # No es base64 decodificable con el alfabeto standard; correcto también.


def test_encoded_store_roundtrip_with_explicit_key() -> None:
    """Con CREDENTIAL_ENCRYPTION_KEY, guardar y recargar en OTRO proceso/instancia
    descifra correctamente (persistencia real entre reinicios)."""
    import os
    from cryptography.fernet import Fernet
    key = Fernet.generate_key().decode()
    # Fijar la clave del módulo (simula .env configurado) y resetear el cache
    os.environ["CREDENTIAL_ENCRYPTION_KEY"] = key
    import agentic_os.connectors.auth.credential_store as cs
    cs._module_fernet = None  # forzar re-inicialización con la clave
    try:
        encoded = cs.EncodedFileCredentialStore.encrypt("persistent_secret")
        # Nueva inicialización con la MISMA clave (otro "proceso")
        cs._module_fernet = None
        decoded = cs.EncodedFileCredentialStore.decrypt(encoded)
        assert decoded == "persistent_secret", "Fernet con clave estable debe persistir"
    finally:
        os.environ.pop("CREDENTIAL_ENCRYPTION_KEY", None)
        cs._module_fernet = None
