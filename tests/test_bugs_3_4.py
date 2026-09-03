import json
import tempfile
import os

from src.agentic_os.connectors.auth.credential_store import EncodedFileCredentialStore


def test_credentials_not_base64():
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        try:
            path = tmp.name
            store = EncodedFileCredentialStore(path=path)
            store.save("tenant1", {"token": "secret123"})
            raw = open(path, 'rb').read()
            assert b"secret123" not in raw
            assert b"c2VjcmV0" not in raw  # base64 of "secret"
            assert store.load("tenant1")["token"] == "secret123"
        finally:
            os.unlink(path)
