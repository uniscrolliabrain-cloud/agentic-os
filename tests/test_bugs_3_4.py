"""Bug 3 (legacy, test original de aider): las credenciales no se persisten
en claro ni en base64 en disco. Actualizado a la API Fernet actual."""
from src.agentic_os.connectors.auth.credential_store import CredentialStore


def test_credentials_not_base64(tmp_path):
    from src.agentic_os.connectors.core.config import CredentialSet

    store = CredentialStore(cred_dir=str(tmp_path))
    cred = CredentialSet(
        provider="google",
        auth_type="oauth2",
        data={"token": "secret123"},
        scopes=["https://www.googleapis.com/auth/gmail.modify"],
    )
    store.save("tenant1", "google", cred)

    saved = list(tmp_path.rglob("google.json"))
    assert saved, "no se persistio el fichero de credenciales"
    raw = saved[0].read_bytes()
    assert b"secret123" not in raw, "credencial en claro en disco"
    assert b"c2VjcmV0" not in raw, "credencial en base64 en disco"

    loaded = store.load("tenant1", "google")
    assert loaded is not None
    token = loaded.data["token"]
    # CredentialSet.data envuelve los valores en Secret: desenvolver con get_secret_value
    real = token.get_secret_value() if hasattr(token, "get_secret_value") else str(token)
    assert real == "secret123"

