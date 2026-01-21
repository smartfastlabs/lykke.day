import os
import re

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def normalize_postgres_url(url: str) -> str:
    """Normalize PostgreSQL URL to use psycopg (v3) driver.

    Converts various PostgreSQL URL formats to postgresql+psycopg://:
    - postgres://         -> postgresql+psycopg://
    - postgresql://       -> postgresql+psycopg://
    - postgresql+psycopg2:// -> postgresql+psycopg://
    - postgresql+asyncpg:// -> postgresql+psycopg://
    """
    if not url:
        return url

    # Pattern to match various postgres URL schemes
    # Captures: postgres, postgresql, postgresql+psycopg2, postgresql+asyncpg, etc.
    pattern = r"^(postgres(?:ql)?(?:\+\w+)?)://"
    replacement = "postgresql+psycopg://"

    return re.sub(pattern, replacement, url)


class Settings(BaseSettings):
    API_PREFIX: str = ""
    API_BASE_URL: str = "https://localhost:8080"
    WEB_DOMAIN: str = "http://localhost:8888"
    DEBUG: bool = False
    VAPID_SECRET_KEY: str = ""
    VAPID_PUBLIC_KEY: str = ""
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_FROM_NUMBER: str = ""
    TWILIO_MESSAGING_SERVICE_SID: str = ""
    MAILGUN_API_KEY: str = ""
    MAILGUN_DOMAIN: str = "https://api.mailgun.net"
    MAILGUN_FROM_EMAIL: str = ""
    GOOGLE_CREDENTIALS_JSON: str = ""
    ENVIRONMENT: str = "development"
    DATA_PATH: str = "../data"
    DATABASE_URL: str = "postgresql+psycopg://localhost/lykke"
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_MAX_CONNECTIONS: int = 50  # Maximum connections in the pool
    SESSION_SECRET: str = ""
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-3-5-haiku-20241022"  # Default to Haiku for cost
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"  # Default to cheaper model
    SMART_NOTIFICATIONS_ENABLED: bool = True  # Feature flag
    SMART_NOTIFICATION_RATE_LIMIT_MINUTES: int = 10  # Prevent spam
    PRINTER_NAME: str = "HP_OfficeJet_Pro_9010_series"
    PVPORCUPINE_ACCESS_KEY: str = ""
    SENTRY_DSN: str = ""

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def fix_database_url(cls, v: str) -> str:
        """Normalize DATABASE_URL to use psycopg (v3) driver."""
        return normalize_postgres_url(v)

    @field_validator("VAPID_SECRET_KEY", "VAPID_PUBLIC_KEY", mode="before")
    @classmethod
    def fix_pem_newlines(cls, v: str) -> str:
        if v:
            return v.replace("\\n", "\n")
        return v

    model_config = SettingsConfigDict(
        env_file=os.getenv("ENV_FILE", ".env"),
        case_sensitive=True,
    )


settings = Settings()
os.environ["ANTHROPIC_API_KEY"] = settings.ANTHROPIC_API_KEY
