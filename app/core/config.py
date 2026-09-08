from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./data/judge.db"
    redis_url: str = "redis://localhost:6379/0"
    submission_queue_name: str = "judge:submissions"
    jwt_secret: SecretStr = SecretStr("replace-this-in-production")
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60
    cors_origins: str = "http://localhost:8000"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
