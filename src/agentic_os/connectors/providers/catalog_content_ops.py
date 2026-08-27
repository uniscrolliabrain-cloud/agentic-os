"""Catálogo de providers de contenido y operaciones web/automation."""

from typing import Any, Dict

PROVIDER_SPECS_CONTENT_OPS: Dict[str, Dict[str, Any]] = {
    "wordpress": {
        "connector_id": "wordpress", "provider": "WordPress", "auth_type": "basic",
        "caps": ["cms.post.create", "cms.post.read", "cms.post.update", "cms.post.delete",
                 "cms.post.publish", "cms.page.create", "cms.page.read", "cms.page.update",
                 "cms.page.publish", "cms.media.upload", "cms.media.read", "cms.media.delete"],
        "extra_env": ["WORDPRESS_SITE_URL"],
        "token_env": "WORDPRESS_APP_PASSWORD",
    },
    "shopify": {
        "connector_id": "shopify", "provider": "Shopify", "auth_type": "bearer",
        "caps": ["commerce.product.create", "commerce.product.read", "commerce.product.update",
                 "commerce.customer.create", "commerce.customer.read", "commerce.customer.update",
                 "commerce.order.read", "commerce.order.update",
                 "commerce.inventory.read", "commerce.inventory.update"],
        "token_env": "SHOPIFY_ACCESS_TOKEN",
        "extra_env": ["SHOPIFY_SHOP_DOMAIN"],
    },
    "cloudflare": {
        "connector_id": "cloudflare", "provider": "Cloudflare", "auth_type": "bearer",
        "caps": ["cloud.dns.record.read", "cloud.dns.record.create", "cloud.dns.record.update",
                 "storage.file.upload", "storage.file.read", "storage.file.delete",
                 "database.query", "cloud.deployment.create"],
        "token_env": "CLOUDFLARE_API_TOKEN",
        "base_url": "https://api.cloudflare.com/client/v4",
    },
    "n8n": {
        "connector_id": "n8n", "provider": "n8n", "auth_type": "bearer",
        "caps": ["automation.workflow.read", "automation.workflow.create", "automation.workflow.update",
                 "automation.workflow.activate", "automation.workflow.deactivate",
                 "automation.workflow.execute", "automation.execution.read"],
        "token_env": "N8N_API_KEY",
        "extra_env": ["N8N_BASE_URL"],
    },
    "notion": {
        "connector_id": "notion", "provider": "Notion", "auth_type": "bearer",
        "caps": ["knowledge.page.create", "knowledge.page.read", "knowledge.page.update",
                 "knowledge.page.search",
                 "database.read", "database.record.create", "database.record.update"],
        "token_env": "NOTION_API_KEY",
        "base_url": "https://api.notion.com/v1",
    },
    "twilio": {
        "connector_id": "twilio", "provider": "Twilio", "auth_type": "basic",
        "caps": ["communication.sms.send", "communication.sms.read",
                 "communication.call.create", "communication.call.read"],
        "extra_env": ["TWILIO_ACCOUNT_SID"],
        "token_env": "TWILIO_AUTH_TOKEN",
    },
    "resend": {
        "connector_id": "resend", "provider": "Resend", "auth_type": "bearer",
        "caps": ["email.message.send", "email.domain.read", "email.event.read"],
        "token_env": "RESEND_API_KEY",
    },
    "smtp_imap": {
        "connector_id": "smtp_imap", "provider": "SMTP/IMAP", "auth_type": "password",
        "caps": ["email.message.read", "email.message.search", "email.message.send",
                 "email.message.reply", "email.draft.create"],
        "extra_env": ["SMTP_HOST", "SMTP_PORT", "IMAP_HOST"],
        "token_env": "EMAIL_APP_PASSWORD",
        "extra_auth_env": ["EMAIL_USERNAME"],
    },
}