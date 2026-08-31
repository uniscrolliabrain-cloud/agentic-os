from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    env: str = Field(default="dev", alias="ENV")
    gemini_api_key: Optional[str] = Field(default=None, alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-3.6-flash", alias="GEMINI_MODEL")
    gemini_chat_model: str = Field(default="gemini-3.6-flash", alias="GEMINI_CHAT_MODEL")
    gemini_temperature: float = Field(default=0.2, alias="GEMINI_TEMPERATURE")

    # --- FASE 0: persistencia (multi-tenant) ---
    eventlog_impl: str = Field(default="jsonl", alias="EVENTLOG_IMPL")
    conversations_dir: str = Field(default="data/conversations")
    eventlog_dir: str = Field(default="data/eventlog")
    policies_dir: str = Field(default="data/policies")
    # Seguridad FASE 1: único disparador del allow-all. ENV=dev NO cambia la
    # semántica de seguridad. Default false (incluso en dev).
    dev_allow_all: bool = Field(default=False, alias="DEV_ALLOW_ALL")

    # --- Credenciales de conectores (las 40 del .env.example) ---
    # Google
    google_client_id: Optional[str] = Field(default=None, alias="GOOGLE_CLIENT_ID")
    google_client_secret: Optional[str] = Field(default=None, alias="GOOGLE_CLIENT_SECRET")
    google_refresh_token: Optional[str] = Field(default=None, alias="GOOGLE_REFRESH_TOKEN")
    google_redirect_uri: Optional[str] = Field(default=None, alias="GOOGLE_REDIRECT_URI")
    # Microsoft
    microsoft_client_id: Optional[str] = Field(default=None, alias="MICROSOFT_CLIENT_ID")
    microsoft_client_secret: Optional[str] = Field(default=None, alias="MICROSOFT_CLIENT_SECRET")
    microsoft_refresh_token: Optional[str] = Field(default=None, alias="MICROSOFT_REFRESH_TOKEN")
    microsoft_tenant_id: Optional[str] = Field(default=None, alias="MICROSOFT_TENANT_ID")
    # OpenAI / Anthropic
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, alias="ANTHROPIC_API_KEY")
    # HubSpot
    hubspot_client_id: Optional[str] = Field(default=None, alias="HUBSPOT_CLIENT_ID")
    hubspot_client_secret: Optional[str] = Field(default=None, alias="HUBSPOT_CLIENT_SECRET")
    hubspot_access_token: Optional[str] = Field(default=None, alias="HUBSPOT_ACCESS_TOKEN")
    hubspot_refresh_token: Optional[str] = Field(default=None, alias="HUBSPOT_REFRESH_TOKEN")
    hubspot_portal_id: Optional[str] = Field(default=None, alias="HUBSPOT_PORTAL_ID")
    # Meta
    meta_app_id: Optional[str] = Field(default=None, alias="META_APP_ID")
    meta_app_secret: Optional[str] = Field(default=None, alias="META_APP_SECRET")
    meta_access_token: Optional[str] = Field(default=None, alias="META_ACCESS_TOKEN")
    meta_page_id: Optional[str] = Field(default=None, alias="META_PAGE_ID")
    meta_ig_user_id: Optional[str] = Field(default=None, alias="META_IG_USER_ID")
    # Slack
    slack_client_id: Optional[str] = Field(default=None, alias="SLACK_CLIENT_ID")
    slack_client_secret: Optional[str] = Field(default=None, alias="SLACK_CLIENT_SECRET")
    slack_signing_secret: Optional[str] = Field(default=None, alias="SLACK_SIGNING_SECRET")
    slack_bot_token: Optional[str] = Field(default=None, alias="SLACK_BOT_TOKEN")
    # WhatsApp / Telegram
    whatsapp_phone_number_id: Optional[str] = Field(default=None, alias="WHATSAPP_PHONE_NUMBER_ID")
    whatsapp_business_account_id: Optional[str] = Field(default=None, alias="WHATSAPP_BUSINESS_ACCOUNT_ID")
    telegram_bot_token: Optional[str] = Field(default=None, alias="TELEGRAM_BOT_TOKEN")
    # GitHub
    github_token: Optional[str] = Field(default=None, alias="GITHUB_TOKEN")
    github_client_id: Optional[str] = Field(default=None, alias="GITHUB_CLIENT_ID")
    github_client_secret: Optional[str] = Field(default=None, alias="GITHUB_CLIENT_SECRET")
    # Stripe
    stripe_secret_key: Optional[str] = Field(default=None, alias="STRIPE_SECRET_KEY")
    stripe_webhook_secret: Optional[str] = Field(default=None, alias="STRIPE_WEBHOOK_SECRET")
    # Shopify
    shopify_api_key: Optional[str] = Field(default=None, alias="SHOPIFY_API_KEY")
    shopify_password: Optional[str] = Field(default=None, alias="SHOPIFY_PASSWORD")
    shopify_access_token: Optional[str] = Field(default=None, alias="SHOPIFY_ACCESS_TOKEN")
    shopify_store_name: Optional[str] = Field(default=None, alias="SHOPIFY_STORE_NAME")
    # WordPress
    wordpress_app_username: Optional[str] = Field(default=None, alias="WORDPRESS_APP_USERNAME")
    wordpress_app_password: Optional[str] = Field(default=None, alias="WORDPRESS_APP_PASSWORD")
    wordpress_site_url: Optional[str] = Field(default=None, alias="WORDPRESS_SITE_URL")
    # Supabase
    supabase_url: Optional[str] = Field(default=None, alias="SUPABASE_URL")
    supabase_key: Optional[str] = Field(default=None, alias="SUPABASE_KEY")
    supabase_service_role_key: Optional[str] = Field(default=None, alias="SUPABASE_SERVICE_ROLE_KEY")
    # Bases de datos
    postgres_dsn: Optional[str] = Field(default=None, alias="POSTGRES_DSN")
    redis_url: Optional[str] = Field(default=None, alias="REDIS_URL")
    # Vercel / Cloudflare
    vercel_token: Optional[str] = Field(default=None, alias="VERCEL_TOKEN")
    cloudflare_api_token: Optional[str] = Field(default=None, alias="CLOUDFLARE_API_TOKEN")
    cloudflare_account_id: Optional[str] = Field(default=None, alias="CLOUDFLARE_ACCOUNT_ID")
    # n8n
    n8n_api_key: Optional[str] = Field(default=None, alias="N8N_API_KEY")
    n8n_base_url: Optional[str] = Field(default=None, alias="N8N_BASE_URL")
    # Twilio / DocuSign / PM
    twilio_account_sid: Optional[str] = Field(default=None, alias="TWILIO_ACCOUNT_SID")
    twilio_auth_token: Optional[str] = Field(default=None, alias="TWILIO_AUTH_TOKEN")
    twilio_from: Optional[str] = Field(default=None, alias="TWILIO_FROM")
    docusign_client_id: Optional[str] = Field(default=None, alias="DOCUSIGN_CLIENT_ID")
    docusign_client_secret: Optional[str] = Field(default=None, alias="DOCUSIGN_CLIENT_SECRET")
    docusign_private_key: Optional[str] = Field(default=None, alias="DOCUSIGN_PRIVATE_KEY")
    notion_api_key: Optional[str] = Field(default=None, alias="NOTION_API_KEY")
    linear_api_key: Optional[str] = Field(default=None, alias="LINEAR_API_KEY")
    clickup_api_key: Optional[str] = Field(default=None, alias="CLICKUP_API_KEY")
    asana_token: Optional[str] = Field(default=None, alias="ASANA_TOKEN")
    jira_token: Optional[str] = Field(default=None, alias="JIRA_TOKEN")
    jira_email: Optional[str] = Field(default=None, alias="JIRA_EMAIL")
    connector_cred_dir: Optional[str] = Field(default="./data/creds", alias="CONNECTOR_CRED_DIR")

settings = Settings()
