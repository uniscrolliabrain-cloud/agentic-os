from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    env: str = "dev"
    
    # Gemini LLM Configuration
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-2.0-flash"
    gemini_temperature: float = 0.2

    # Google Auth & Workspace Configuration
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    google_allowed_domains: List[str] = Field(default_factory=list)
    google_workspace_scopes: List[str] = Field(
        default_factory=lambda: [
            "openid",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/gmail.send",
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/calendar.events",
            "https://www.googleapis.com/auth/drive.readonly",
        ]
    )
    auth_disabled: bool = False


