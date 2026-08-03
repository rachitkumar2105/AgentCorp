from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "AgentCorp API"
    APP_DESCRIPTION: str = "AI Powered Virtual Company"
    APP_VERSION: str = "0.1.0"

    DEBUG: bool = True

    HOST: str = "127.0.0.1"
    PORT: int = 8000

    DATABASE_URL: str = "sqlite:///./test.db"

    SECRET_KEY: str = "changeme-secret"

    # AI Provider Settings
    DEFAULT_PROVIDER: str = "groq"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"

    # Security & Rate Limiting
    RATE_LIMIT_MAX_REQUESTS: int = 60          # requests per minute per user/IP
    RATE_LIMIT_WINDOW_SECONDS: int = 60        # window size in seconds
    QUOTA_DEFAULT_LIMIT: int = 1_000_000       # default AI tokens per period

    # Encryption (key loaded from SECRET_BACKEND via secret_manager)
    SECRET_BACKEND: str = "env"                # env | vault | aws | azure | gcp
    SECRET_VAULT_URL: str = "http://localhost:8200"

    # Data Governance
    DATA_RETENTION_DAYS: int = 365             # default retention period
    PURGE_GRACE_DAYS: int = 30                 # days after soft-delete before hard purge

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()