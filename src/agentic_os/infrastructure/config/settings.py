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
    gemini_model: str = Field(default="gemini-2.0-flash", alias="GEMINI_MODEL")
    gemini_chat_model: str = Field(default="gemini-2.0-flash", alias="GEMINI_CHAT_MODEL")
    gemini_temperature: float = Field(default=0.2, alias="GEMINI_TEMPERATURE")
    connector_cred_dir: Optional[str] = Field(default="./data/creds", alias="CONNECTOR_CRED_DIR")
    google_client_id: Optional[str] = Field(default=None, alias="GOOGLE_CLIENT_ID")
    google_client_secret: Optional[str] = Field(default=None, alias="GOOGLE_CLIENT_SECRET")
    google_refresh_token: Optional[str] = Field(default=None, alias="GOOGLE_REFRESH_TOKEN")
    microsoft_client_id: Optional[str] = Field(default=None, alias="MICROSOFT_CLIENT_ID")
    hubspot_access_token: Optional[str] = Field(default=None, alias="HUBSPOT_ACCESS_TOKEN")
    github_token: Optional[str] = Field(default=None, alias="GITHUB_TOKEN")
    stripe_secret_key: Optional[str] = Field(default=None, alias="STRIPE_SECRET_KEY")

settings = Settings()
