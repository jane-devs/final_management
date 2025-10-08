from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    database_url: str
    secret_key: str = os.getenv("SECRET_KEY", "fallbacksecret")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    environment: str = "development"

    class Config:
        env_file = ".env"


settings = Settings()
