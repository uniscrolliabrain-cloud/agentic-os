from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    env: str = "dev"
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-3.6-flash"
    gemini_chat_model: str = "gemini-3.6-flash"
    gemini_temperature: float = 0.2
    connector_cred_dir: Optional[str] = None
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    google_refresh_token: Optional[str] = None
    microsoft_client_id: Optional[str] = None
    hubspot_access_token: Optional[str] = None
    github_token: Optional[str] = None
    stripe_secret_key: Optional[str] = None
