"""Registry de providers pre-registrados.

Define, para cada provider, sus capabilities canónicas, tipo de auth y qué
variables de entorno leer para cargar credenciales reales cuando se conecte.
Nunca contiene credenciales reales: el código solo provee la estructura.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from ..core.config import ConnectorConfig
from ..factory import ConnectorFactory
from .stub import StubConnector

# Especificaciones de todos los providers del catálogo.
# Cada provider declara: capabilities, auth_type, oauth config y/o env keys
# para cargar credenciales reales cuando se conecta.
PROVIDER_SPECS: Dict[str, Dict[str, Any]] = {
    "google": {
        "connector_id": "google",
        "provider": "Google",
        "auth_type": "oauth2",
        "caps": [
            "email.message.read", "email.message.send",
            "file.read", "file.create",
            "calendar.event.create", "calendar.event.read",
            "video.upload", "analytics.metrics.get", "analytics.search.query",
        ],
        "oauth": {
            "client_id_env": "GOOGLE_CLIENT_ID",
            "client_secret_env": "GOOGLE_CLIENT_SECRET",
            "refresh_token_env": "GOOGLE_REFRESH_TOKEN",
            "redirect_uri_env": "GOOGLE_REDIRECT_URI",
            "authorization_url": "https://accounts.google.com/o/oauth2/auth",
            "token_url": "https://oauth2.googleapis.com/token",
            "scopes": [
                "https://www.googleapis.com/auth/gmail.modify",
                "https://www.googleapis.com/auth/drive.file",
                "https://www.googleapis.com/auth/calendar",
                "https://www.googleapis.com/auth/youtube.upload",
                "https://www.googleapis.com/auth/analytics.readonly",
            ],
        },
    },
    "openai": {
        "connector_id": "openai", "provider": "OpenAI", "auth_type": "bearer",
        "caps": ["ai.text.generate", "ai.image.generate", "ai.text.embed"],
        "token_env": "OPENAI_API_KEY",
    },
    "anthropic": {
        "connector_id": "anthropic", "provider": "Anthropic", "auth_type": "bearer",
        "caps": ["ai.text.generate", "ai.text.extract", "ai.text.classify"],
        "token_env": "ANTHROPIC_API_KEY",
    },
    "hubspot": {
        "connector_id": "hubspot", "provider": "HubSpot", "auth_type": "oauth2",
        "caps": ["crm.contact.create", "crm.contact.read", "crm.contact.update",
                 "crm.company.create", "crm.company.read", "crm.deal.create", "crm.deal.read",
                 "crm.task.create", "crm.task.update", "crm.note.create", "crm.pipeline.read"],
        "oauth": {"client_id_env": "HUBSPOT_CLIENT_ID", "client_secret_env": "HUBSPOT_CLIENT_SECRET",
                  "token_url": "https://api.hubapi.com/oauth/v1/token", "redirect_uri_env": "HUBSPOT_REDIRECT_URI",
                  "scopes": ["crm", "automation", "sales"]},
        "token_env": "HUBSPOT_ACCESS_TOKEN",
    },
    "github": {
        "connector_id": "github", "provider": "GitHub", "auth_type": "bearer",
        "caps": ["software.repository.read", "software.repository.create",
                 "software.file.read", "software.file.create", "software.file.update",
                 "software.branch.create", "software.commit.create",
                 "software.pull_request.create", "software.pull_request.merge",
                 "software.issue.create", "software.issue.update", "software.release.create",
                 "software.workflow.trigger"],
        "token_env": "GITHUB_TOKEN",
    },
    "stripe": {
        "connector_id": "stripe", "provider": "Stripe", "auth_type": "bearer",
        "caps": ["finance.customer.create", "finance.customer.read",
                 "commerce.product.create", "commerce.product.read",
                 "finance.payment_link.create", "finance.invoice.create", "finance.invoice.read",
                 "finance.invoice.send", "finance.subscription.create", "finance.subscription.read",
                 "finance.subscription.update", "finance.refund.create"],
        "token_env": "STRIPE_SECRET_KEY",
    },
    "vercel": {
        "connector_id": "vercel", "provider": "Vercel", "auth_type": "bearer",
        "caps": ["cloud.project.read", "cloud.project.create",
                 "cloud.deployment.create", "cloud.deployment.read",
                 "cloud.deployment.cancel", "cloud.deployment.rollback",
                 "cloud.environment.read", "cloud.environment.update",
                 "cloud.domain.read", "cloud.domain.configure"],
        "token_env": "VERCEL_TOKEN",
    },
    "slack": {
        "connector_id": "slack", "provider": "Slack", "auth_type": "bearer",
        "caps": ["communication.message.send", "communication.channel.read",
                 "communication.message.search", "communication.file.upload"],
        "token_env": "SLACK_BOT_TOKEN",
    },
}

# Catalogos por familia (todos declarados, ninguno conectado).
from .catalog_ai_web import PROVIDER_SPECS_AI_WEB
from .catalog_comms_social import PROVIDER_SPECS_COMMS_SOCIAL
from .catalog_content_ops import PROVIDER_SPECS_CONTENT_OPS
from .catalog_data_voice import PROVIDER_SPECS_DATA_VOICE

PROVIDER_SPECS.update(PROVIDER_SPECS_AI_WEB)
PROVIDER_SPECS.update(PROVIDER_SPECS_COMMS_SOCIAL)
PROVIDER_SPECS.update(PROVIDER_SPECS_CONTENT_OPS)
PROVIDER_SPECS.update(PROVIDER_SPECS_DATA_VOICE)


def register_builtin_providers(factory: ConnectorFactory) -> None:
    """Registra builders para todos los providers del catálogo (SIN credenciales)."""
    for provider, spec in PROVIDER_SPECS.items():
        def _builder(
            cid=spec["connector_id"], prov=spec["provider"],
            caps=list(spec["caps"]), auth=spec.get("auth_type", "none"),
            oauth_cfg=spec.get("oauth"), token_env=spec.get("token_env"),
            base_cfg={"base_url": spec.get("base_url"), "note": spec.get("note")},
            config=None, credentials=None, connected=False,
        ) -> StubConnector:
            merged_cfg = {k: v for k, v in base_cfg.items() if v}
            if config:
                merged_cfg.update(config)
            return StubConnector(
                connector_id=cid, provider=prov, capabilities=caps,
                auth_type=auth, oauth=oauth_cfg,
                config=merged_cfg, credentials=credentials, connected=connected,
            )
        factory.register_builder(provider, _builder)


def get_provider_spec(provider: str) -> Optional[Dict[str, Any]]:
    return PROVIDER_SPECS.get(provider)


def get_provider_capabilities(provider: str) -> List[str]:
    spec = PROVIDER_SPECS.get(provider)
    return list(spec["caps"]) if spec else []


def load_provider_credentials(provider: str, workspace: str = "default") -> Optional[Dict[str, Any]]:
    """Carga credenciales reales desde CredentialStore o .env → para inyectar al connector."""
    spec = PROVIDER_SPECS.get(provider)
    if not spec:
        return None
    from ..auth.credential_store import CredentialStore
    from ...infrastructure.config.settings import Settings
    settings = Settings()
    # 1) CredentialStore (encriptado en disco)
    cred_store = CredentialStore()
    cred = cred_store.load(workspace, provider)
    if cred and cred.valid:
        return dict(cred.data) if isinstance(cred.data, dict) else cred.data
    # 2) fallback: variables de entorno
    env_keys: list[str] = []
    if spec.get("oauth"):
        for k in ["client_id_env", "client_secret_env", "refresh_token_env", "redirect_uri_env"]:
            ek = spec["oauth"].get(k)
            if ek:
                env_keys.append(ek)
    if spec.get("token_env"):
        env_keys.append(spec["token_env"])
    loaded = {}
    for k in env_keys:
        val = os.environ.get(k) or getattr(settings, k.lower(), None)
        if val:
            loaded[k] = val
    return loaded if loaded else None
