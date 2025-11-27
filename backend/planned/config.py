import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    API_PREFIX: str = ""
    TIMEZONE: str = "America/Chicago"
    DEBUG: bool = False

    VAPID_SECRET_KEY: str = ""
    VAPID_PUBLIC_KEY: str = ""
    ENVIRONMENT: str = "development"
    DATA_PATH: str = "../data"
    SESSION_SECRET: str = ""

    model_config = SettingsConfigDict(
        env_file=os.getenv("ENV_FILE", ".env"),
        case_sensitive=True,
    )


settings = Settings()
