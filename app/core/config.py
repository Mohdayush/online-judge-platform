from pydantic import SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./judge.db"
    jwt_secret: SecretStr = SecretStr("replace-this-in-production")
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60


settings = Settings()
