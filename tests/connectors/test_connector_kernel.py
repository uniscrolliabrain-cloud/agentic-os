"""Catálogo y registro: todos los conectores existen SIN conectar."""

import asyncio

import pytest

from agentic_os.connectors import CapabilityRegistry, ConnectorFactory
from agentic_os.connectors.providers import (
    PROVIDER_SPECS,
    get_provider_capabilities,
    register_builtin_providers,
)

ESPERADOS = {
    "google", "openai", "anthropic", "hubspot", "github", "stripe", "vercel",
    "slack", "microsoft", "salesforce", "pipedrive", "whatsapp", "telegram",
    "meta", "linkedin", "tiktok", "wordpress", "shopify", "cloudflare",
    "n8n", "notion", "tavily", "serpapi", "exa", "brave_search",
    "firecrawl", "jina_reader", "browser", "twilio", "resend", "smtp_imap",
    "elevenlabs", "docusign", "storage_s3", "supabase_storage", "postgres",
    "redis", "mongodb", "linear", "clickup", "asana", "jira", "vapi", "retell",
}


@pytest.fixture()
def factory() -> ConnectorFactory:
    f = ConnectorFactory()
    register_builtin_providers(f)
    return f


@pytest.fixture()
def registry(factory) -> CapabilityRegistry:
    reg = CapabilityRegistry()
    for provider in PROVIDER_SPECS:
        reg.register(factory.create(provider))
    return reg


def test_catalogo_completo_registrado():
    assert ESPERADOS <= set(PROVIDER_SPECS), (
        f"Faltan providers: {ESPERADOS - set(PROVIDER_SPECS)}"
    )
    assert len(PROVIDER_SPECS) >= 44


def test_todos_los_connectors_nacen_sin_conectar(factory):
    for provider in PROVIDER_SPECS:
        conn = factory.create(provider)
        assert conn.connected is False, provider
        assert conn.capabilities, provider


def test_capabilities_cubren_familias_del_sop(registry):
    caps = {c for conn in registry.list_connectors() for c in conn.capabilities}
    for familia in ["ai.text.generate", "web.search", "browser.navigate",
                    "email.message.send", "communication.message.send",
                    "storage.file.upload", "database.query", "crm.contact.create",
                    "social.post.publish", "cms.post.create", "commerce.product.read",
                    "software.pull_request.create", "automation.workflow.execute",
                    "finance.refund.create", "voice.call.create",
                    "document.signature.request", "knowledge.page.search"]:
        assert familia in caps, familia


def test_spec_coherente_por_provider():
    for provider, spec in PROVIDER_SPECS.items():
        assert spec["connector_id"] == provider
        assert len(spec["caps"]) > 0


def test_registry_resuelve_multi_provider(registry):
    ids = sorted(c.connector_id for c in registry.resolve("email.message.send"))
    assert {"google", "smtp_imap", "resend", "microsoft"} & set(ids)


def test_health_check_stubs_auth_required(registry):
    for conn in registry.list_connectors():
        health = asyncio.run(conn.health_check())
        assert health.status == "AUTH_REQUIRED", conn.connector_id


def test_get_provider_capabilities():
    caps = get_provider_capabilities("stripe")
    assert "finance.payment_link.create" in caps
    assert get_provider_capabilities("no_existe") == []
