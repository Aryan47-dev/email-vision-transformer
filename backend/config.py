from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    google_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    google_cloud_vision_api_key: str = ""
    max_upload_bytes: int = 10 * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
