import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


def get_env_file() -> str:
    return ".env.development"

class Settings(BaseSettings):

    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    OPENAI_API_BASE: str = "https://api.openai.com/v1"

    DATABASE_URL: str # For async application operations
    SYNC_DATABASE_URL: Optional[str] = None # For synchronous Alembic operations

    ROOT_PASSWORD: str = "root"

    model_config = SettingsConfigDict(
        env_file_encoding='utf-8',
        extra='ignore',
        populate_by_name=True
    )

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT.lower() == "development"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

settings = Settings(_env_file=get_env_file())
