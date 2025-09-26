from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    secret_key: str
    environment: str = "development"

    class Config:
        env_file = ".env"


settings = Settings()
