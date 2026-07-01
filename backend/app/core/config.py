from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "bridge-backend"
    environment: str = "development"
    database_url: str = "postgresql+psycopg://bridge:bridge@localhost:5432/bridge"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: str = "dev-secret-change-me"


@lru_cache
def get_settings() -> Settings:
    return Settings()
