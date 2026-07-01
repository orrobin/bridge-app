from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "bridge-backend"
    environment: str = "development"
    database_url: str = "postgresql+psycopg://bridge:bridge@localhost:5432/bridge"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: str = "dev-secret-change-me"
    # Comma-separated (not JSON) so it's easy to set from a hosting provider's env var UI.
    cors_allowed_origins_raw: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def cors_allowed_origins(self) -> list[str]:
        origins = self.cors_allowed_origins_raw.split(",")
        return [origin.strip() for origin in origins if origin.strip()]

    anthropic_api_key: str = ""
    openai_api_key: str = ""
    # Tiered per SAD Phase 8.1: cheap/fast model for safety classification and
    # routing, frontier model for the user-facing empathy/strategy reasoning.
    safety_model: str = "claude-haiku-4-5-20251001"
    generation_model: str = "claude-sonnet-5"
    embedding_model: str = "text-embedding-3-small"
    # Off by default: the heuristic providers need no API credits. Flip once
    # Anthropic API credits are available (TASKS.md T6.1/T7).
    use_llm_safety_classifier: bool = False
    use_llm_agents: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
