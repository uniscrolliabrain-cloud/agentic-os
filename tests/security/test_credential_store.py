"""Tests del CredentialStore (#16 del hardening).

- missing credential → None (no excepción, no secreto inventado)
- aislamiento por workspace (tenant isolation)
- credencial malformada → no crashea
- roundtrip de SecretStr (el fix del bug de str(Secret) = '**********')
- base64 ≠ cifrado: el fichero en disco contiene el valor codificado, nunca
  se presenta como cifrado.
"""
from __future__ import annotations

import base64
import json

import pytest

from agentic_os.connectors.auth.credential_store import (
    CredentialStore,
    EncodedFileCredentialStore,
)
from agentic_os.connectors.core.config import CredentialSet


@pytest.fixture()
def store(tmp_path):
    return CredentialStore(cred_dir=str(tmp_path / "creds"))


def _cred(provider: str = "gmail", token: str = "tok-secreto-123") -> CredentialSet:
    return CredentialSet(provider=provider, auth_type="bearer", data={"token": token})


def test_missing_credential_devuelve_none(store) -> None:
    assert store.load("ws-a", "gmail") is None


def test_roundtrip_secretstr(store) -> None:
    store.save("ws-a", "gmail", _cred(token="ABC-xyz-123"))
    cred = store.load("ws-a", "gmail")
    assert cred is not None
    # CredentialSet.data son Secret[str]: desenvolver con get_secret_value()
    assert cred.data["token"].get_secret_value() == "ABC-xyz-123"  # NO "**********"


def test_tenant_isolation_entre_workspaces(store, tmp_path) -> None:
    store.save("ws-a", "gmail", _cred(token="token-de-A"))
    store.save("ws-b", "gmail", _cred(token="token-de-B"))

    a = store.load("ws-a", "gmail")
    b = store.load("ws-b", "gmail")
    assert a.data["token"].get_secret_value() == "token-de-A"
    assert b.data["token"].get_secret_value() == "token-de-B"
    # ws-c no ve nada de A
    assert store.load("ws-c", "gmail") is None
    # el fichero de A no contiene el token de B
    raw_a = (tmp_path / "creds" / "ws-a" / "gmail.json").read_text(encoding="utf-8")
    assert "token-de-B" not in raw_a


def test_delete(store) -> None:
    store.save("ws-a", "gmail", _cred())
    assert store.delete("ws-a", "gmail") is True
    assert store.load("ws-a", "gmail") is None
    assert store.delete("ws-a", "gmail") is False


def test_credential_malformada_no_crashea(store, tmp_path) -> None:
    p = tmp_path / "creds" / "ws-x"
    p.mkdir(parents=True)
    (p / "gmail.json").write_text("esto no es json{{{", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        store.load("ws-x", "gmail")
    # y con base64 corrupto en data → decrypt devuelve "" sin lanzar
    (p / "gmail.json").write_text(
        json.dumps({"provider": "gmail", "auth_type": "bearer", "data": {"token": "!!!no-b64!!!"}}),
        encoding="utf-8",
    )
    cred = store.load("ws-x", "gmail")
    assert cred is not None
    assert cred.data["token"].get_secret_value() == ""


def test_base64_no_es_cifrado_documentado(tmp_path) -> None:
    """El disco contiene base64 (reversible sin clave): el contrato debe ser
    honesto — es codificación, no cifrado."""
    enc = EncodedFileCredentialStore.encrypt("secreto")
    assert base64.b64decode(enc) == b"secreto"  # reversible sin clave
    doc = EncodedFileCredentialStore.__doc__ or ""
    assert "NO es encriptación" in doc


def test_encrypted_alias_de_encode_no_confunde(store, tmp_path) -> None:
    store.save("ws-a", "gmail", _cred(token="valor"))
    raw = (tmp_path / "creds" / "ws-a" / "gmail.json").read_text(encoding="utf-8")
    assert "valor" not in raw  # al menos no está en claro
    assert base64.b64encode(b"valor").decode() in raw  # pero sí reversible
