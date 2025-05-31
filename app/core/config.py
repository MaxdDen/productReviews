from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):

    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    OPENAI_API_BASE: str = "https://api.openai.com/v1"

    DATABASE_URL: str

    ROOT_PASSWORD: str = "root"

    model_config = SettingsConfigDict(env_file_encoding='utf-8')

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT.lower() == "development"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

# Выбор нужного .env-файла
env_file = ".env.production" if os.getenv("ENVIRONMENT") == "production" else ".env.development"
settings = Settings(_env_file=env_file)