import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    API_PREFIX: str = ""
    TIMEZONE: str = "America/Chicago"
    DEBUG: bool = False

    VAPID_SECRET_KEY: str = ""
    VAPID_PUBLIC_KEY: str = ""
    ENVIRONMENT: str = "development"
    DATA_PATH: str = "../data"

    class Config:
        # Default to ".env", but allow overriding with ENV_FILE
        env_file = os.getenv("ENV_FILE", ".env")
        case_sensitive = True


settings = Settings()
