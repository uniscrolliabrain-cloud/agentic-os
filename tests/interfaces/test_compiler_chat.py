"""Tests del chat del compilador (FASE 2 â€” PLAN_CLINE_AGENTE_COMPILADOR.md).

Verifican el contrato del modo PLAN: el compilador propone un blueprint y pide
el Gate 1, pero **nunca escribe**. El proveedor LLM se fuerza a offline para que
la suite sea determinista y no toque la red.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from agentic_os.infrastructure.tenancy import TenantRegistry
from agentic_os.interfaces.api import rest

COMPILER = "agentic-compiler"
BOR = "bor-agencia"
URL = f"/api/v1/tenants/{COMPILER}/chat"
IDEA = (
    "Quiero un OS agentico para mi clinica dental: "
    "citas, recordatorios y facturacion"
)
WRITE_MESSAGE = (
    "Escribe el fichero del blueprint y haz push a la rama. Ademas abre el PR."
)
REPO_ROOT = Path(__file__).resolve().parents[2]


def _api_key(slug: str) -> str:
    # Reset singleton: otros tests (test_bug19) lo dejan apuntando
    # a un registry temporal ya desaparecido. Aqui forzamos uno
    # fresco que lee del registry.json real del repo.
    TenantRegistry._SHARED_INSTANCE = None
    tenant = TenantRegistry().get(slug)
    assert tenant is not None, f"el tenant {slug} debe existir en registry.json"
    return tenant.config.credentials["api_key"]


@pytest.fixture(autouse=True)
def _offline(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """CWD en el repo, sin DEV_ALLOW_ALL y sin LLM real (offline determinista)."""
    monkeypatch.chdir(REPO_ROOT)
    monkeypatch.delenv("DEV_ALLOW_ALL", raising=False)
    monkeypatch.setattr(rest, "TENANTS_DATA_DIR", tmp_path / "tenants")
    monkeypatch.setattr(rest, "_compiler_llm", lambda: None)
    return tmp_path / "tenants"


@pytest.fixture()
def client() -> TestClient:
    return TestClient(rest.app)


@pytest.fixture()
def compiler_headers() -> dict:
    return {"X-Tenant-Id": COMPILER, "X-Api-Key": _api_key(COMPILER)}


def test_chat_responde_en_modo_plan(client: TestClient, compiler_headers: dict) -> None:
    resp = client.post(URL, json={"message": IDEA}, headers=compiler_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["mode"] == "plan"
    assert body["tenant_id"] == COMPILER
    assert body["provider"] == "offline"
    assert body["gate"] == "gate_1"
    assert body["write_decision"] == "require_approval"
    assert body["event_id"]
    assert "Gate 1" in body["reply"]

    blueprint = body["blueprint"]
    assert blueprint["status"] == "proposed"
    assert blueprint["mode"] == "plan"
    assert blueprint["domain"] == "clinic"
    assert "clinic.appointment" in blueprint["entities"]
    assert "calendar.event.create" in blueprint["capabilities"]
    assert blueprint["policy"]["calendar.event.create"] == "require_approval"
    assert blueprint["phases"]


def test_no_genera_intents_de_escritura(
    client: TestClient, compiler_headers: dict, _offline: Path
) -> None:
    resp = client.post(URL, json={"message": WRITE_MESSAGE}, headers=compiler_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["discarded_intents"] == ["repo.file.write", "git.push", "git.pr.create"]
    assert "Nada se ha escrito" in body["reply"]
    # El blueprint sigue siendo una propuesta: nada se ha aplicado.
    assert body["blueprint"]["status"] == "proposed"
    # Y en el data_dir del tenant solo existe el chat (cero escrituras de cÃ³digo).
    assert sorted(p.name for p in (_offline / COMPILER).iterdir()) == ["chat"]


def test_esqueleto_offline_es_determinista(
    client: TestClient, compiler_headers: dict
) -> None:
    first = client.post(URL, json={"message": IDEA}, headers=compiler_headers).json()
    second = client.post(URL, json={"message": IDEA}, headers=compiler_headers).json()
    for key in ("slug", "domain", "tenant_name", "entities", "capabilities", "policy"):
        assert first["blueprint"][key] == second["blueprint"][key]


def test_conversacion_persistida_en_el_data_dir_del_tenant(
    client: TestClient, compiler_headers: dict, _offline: Path
) -> None:
    first = client.post(URL, json={"message": IDEA}, headers=compiler_headers).json()
    conv_id = first["conversation_id"]
    assert conv_id

    second = client.post(
        URL,
        json={"message": "anade recordatorios por whatsapp", "conversation_id": conv_id},
        headers=compiler_headers,
    ).json()
    assert second["conversation_id"] == conv_id

    path = _offline / COMPILER / "chat" / f"{conv_id}.json"
    conv = json.loads(path.read_text(encoding="utf-8"))
    assert conv["tenant_id"] == COMPILER
    assert conv["mode"] == "plan"
    assert [m["role"] for m in conv["messages"]] == [
        "user",
        "assistant",
        "user",
        "assistant",
    ]
    assert conv["messages"][0]["content"] == IDEA


def test_conversacion_inexistente_404(client: TestClient, compiler_headers: dict) -> None:
    resp = client.post(
        URL,
        json={"message": IDEA, "conversation_id": "chat_no_existe_123"},
        headers=compiler_headers,
    )
    assert resp.status_code == 404


def test_aislamiento_por_tenant(client: TestClient) -> None:
    # Sin cabeceras el scope es "system": no puede hablar como el compilador.
    assert client.post(URL, json={"message": IDEA}).status_code == 403
    # Con el tenant de otra agencia, tampoco.
    other = client.post(
        URL,
        json={"message": IDEA},
        headers={"X-Tenant-Id": BOR, "X-Api-Key": _api_key(BOR)},
    )
    assert other.status_code == 403


def test_sin_api_key_del_tenant_401(client: TestClient) -> None:
    resp = client.post(URL, json={"message": IDEA}, headers={"X-Tenant-Id": COMPILER})
    assert resp.status_code == 401


def test_mensaje_vacio_400(client: TestClient, compiler_headers: dict) -> None:
    resp = client.post(URL, json={"message": "   "}, headers=compiler_headers)
    assert resp.status_code == 400


def test_policy_denegada_corta_el_chat(
    client: TestClient, compiler_headers: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    from agentic_os.kernel.policy.evaluator import Decision

    monkeypatch.setattr(
        rest._policy_engine,
        "decide",
        lambda *a, **k: Decision(effect="deny", reason="test: sin blueprint"),
    )
    resp = client.post(URL, json={"message": IDEA}, headers=compiler_headers)
    assert resp.status_code == 403
    assert "policy deniega" in resp.json()["detail"]


class _FakeLLM:
    """Provider de prueba: devuelve un blueprint vÃ¡lido en JSON."""

    def generate(self, prompt: str, system_instruction=None) -> str:
        assert system_instruction  # la persona del compilador siempre se inyecta
        return json.dumps(
            {
                "slug": "veterinaria-norte",
                "tenant_name": "Veterinaria Norte",
                "domain": "vet",
                "entities": ["vet.pet", "vet.appointment"],
                "capabilities": ["calendar.event.create", "whatsapp.message.send"],
            }
        )


def test_usa_el_llm_real_cuando_existe(
    client: TestClient, compiler_headers: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(rest, "_compiler_llm", lambda: _FakeLLM())
    body = client.post(URL, json={"message": IDEA}, headers=compiler_headers).json()
    assert body["provider"] == "_FakeLLM"
    assert body["blueprint"]["slug"] == "veterinaria-norte"
    assert body["blueprint"]["domain"] == "vet"


def test_llm_ilegible_cae_al_esqueleto_offline(
    client: TestClient, compiler_headers: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    class _BrokenLLM:
        def generate(self, prompt: str, system_instruction=None) -> str:
            return "esto no es json"

    monkeypatch.setattr(rest, "_compiler_llm", lambda: _BrokenLLM())
    body = client.post(URL, json={"message": IDEA}, headers=compiler_headers).json()
    assert body["provider"] == "offline"
    assert body["blueprint"]["slug"] == "clinica"


def test_otro_tenant_no_tiene_chat_de_compilador(
    client: TestClient, compiler_headers: dict
) -> None:
    resp = client.post(
        f"/api/v1/tenants/{BOR}/chat",
        json={"message": IDEA},
        headers={"X-Tenant-Id": BOR, "X-Api-Key": _api_key(BOR)},
    )
    assert resp.status_code == 404