from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    tavily_api_key: str = ""
    database_url: str = "sqlite:///./data/demo.db"
    frontend_origin: str = "http://localhost:3000"
    livekit_url: str = ""
    livekit_api_key: str = ""
    livekit_api_secret: str = ""
    sarvam_api_key: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
