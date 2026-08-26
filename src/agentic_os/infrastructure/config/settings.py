from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    env: str = "dev"
    gemini_api_key: Optional[str] = None
    # Modelo de orquestación (back office): propone Intents + ejecuta policies
    gemini_model: str = "gemini-3.6-flash"
    # Modelo del asistente frontal (PR): con el que habla el usuario, debe ser rápido
    gemini_chat_model: str = "gemini-3.6-flash"
    gemini_temperature: float = 0.2

