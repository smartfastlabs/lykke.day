import os

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    API_PREFIX: str = ""
    TIMEZONE: str = "America/Chicago"
    DEBUG: bool = False
    VAPID_SECRET_KEY: str = ""
    VAPID_PUBLIC_KEY: str = ""
    ENVIRONMENT: str = "development"
    DATA_PATH: str = "../data"
    DATABASE_URL: str = "postgresql+psycopg://localhost/planned"
    REDIS_URL: str = "redis://localhost:6379"
    SESSION_SECRET: str = ""
    ANTHROPIC_API_KEY: str = ""
    PRINTER_NAME: str = "HP_OfficeJet_Pro_9010_series"
    PVPORCUPINE_ACCESS_KEY: str = ""

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
