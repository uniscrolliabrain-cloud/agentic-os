"""Catálogo de providers de comunicación y social (stubs sin conectar)."""

from typing import Any, Dict

PROVIDER_SPECS_COMMS_SOCIAL: Dict[str, Dict[str, Any]] = {
    "microsoft": {
        "connector_id": "microsoft", "provider": "Microsoft Graph", "auth_type": "oauth2",
        "caps": ["email.message.read", "email.message.send",
                 "calendar.event.create", "calendar.event.read", "calendar.event.delete",
                 "file.read", "file.create", "file.update", "file.delete",
                 "spreadsheet.read", "spreadsheet.write", "communication.message.send"],
        "oauth": {"client_id_env": "MICROSOFT_CLIENT_ID", "client_secret_env": "MICROSOFT_CLIENT_SECRET",
                  "redirect_uri_env": "MICROSOFT_REDIRECT_URI",
                  "authorization_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
                  "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
                  "scopes": ["Mail.ReadWrite", "Calendars.ReadWrite", "Files.ReadWrite", "Chat.Send"]},
    },
    "salesforce": {
        "connector_id": "salesforce", "provider": "Salesforce", "auth_type": "oauth2",
        "caps": ["crm.contact.create", "crm.contact.read", "crm.contact.update", "crm.contact.search",
                 "crm.company.create", "crm.company.read", "crm.deal.create", "crm.deal.read",
                 "crm.task.create", "crm.note.create"],
        "oauth": {"client_id_env": "SALESFORCE_CLIENT_ID", "client_secret_env": "SALESFORCE_CLIENT_SECRET",
                  "authorization_url": "https://login.salesforce.com/services/oauth2/authorize",
                  "token_url": "https://login.salesforce.com/services/oauth2/token"},
        "token_env": "SALESFORCE_ACCESS_TOKEN",
    },
    "pipedrive": {
        "connector_id": "pipedrive", "provider": "Pipedrive", "auth_type": "api_key",
        "caps": ["crm.contact.create", "crm.contact.read", "crm.company.create", "crm.company.read",
                 "crm.deal.create", "crm.deal.read", "crm.deal.update",
                 "crm.note.create", "crm.task.create"],
        "token_env": "PIPEDRIVE_API_TOKEN",
    },
    "whatsapp": {
        "connector_id": "whatsapp", "provider": "WhatsApp Business", "auth_type": "bearer",
        "caps": ["whatsapp.message.send", "whatsapp.template.send",
                 "whatsapp.media.send", "whatsapp.message.receive"],
        "token_env": "WHATSAPP_ACCESS_TOKEN",
        "extra_env": ["WHATSAPP_PHONE_NUMBER_ID"],
        "base_url": "https://graph.facebook.com/v21.0",
    },
    "telegram": {
        "connector_id": "telegram", "provider": "Telegram", "auth_type": "bearer",
        "caps": ["telegram.message.send", "telegram.message.receive",
                 "telegram.file.send", "telegram.file.receive"],
        "token_env": "TELEGRAM_BOT_TOKEN",
        "base_url": "https://api.telegram.org/bot{token}",
    },
    "meta": {
        "connector_id": "meta", "provider": "Meta", "auth_type": "oauth2",
        "caps": ["social.post.create", "social.post.publish", "social.post.delete",
                 "social.comment.read", "social.comment.reply", "social.metrics.get",
                 "ads.campaign.create", "ads.campaign.update", "ads.campaign.pause",
                 "ads.insights.get"],
        "oauth": {"client_id_env": "META_APP_ID", "client_secret_env": "META_APP_SECRET",
                  "authorization_url": "https://www.facebook.com/v21.0/dialog/oauth",
                  "token_url": "https://graph.facebook.com/v21.0/oauth/access_token"},
    },
    "linkedin": {
        "connector_id": "linkedin", "provider": "LinkedIn", "auth_type": "oauth2",
        "caps": ["social.post.create", "social.post.publish", "social.metrics.get"],
        "oauth": {"client_id_env": "LINKEDIN_CLIENT_ID", "client_secret_env": "LINKEDIN_CLIENT_SECRET",
                  "authorization_url": "https://www.linkedin.com/oauth/v2/authorization",
                  "token_url": "https://www.linkedin.com/oauth/v2/accessToken"},
    },
    "tiktok": {
        "connector_id": "tiktok", "provider": "TikTok", "auth_type": "oauth2",
        "caps": ["social.post.publish", "social.metrics.get"],
        "oauth": {"client_id_env": "TIKTOK_CLIENT_KEY", "client_secret_env": "TIKTOK_CLIENT_SECRET",
                  "authorization_url": "https://www.tiktok.com/v2/auth/authorize/",
                  "token_url": "https://open.tiktokapis.com/v2/oauth/token/"},
    },
}