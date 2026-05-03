from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "history"
    mongo_url: str = "mongodb://localhost:27017/?replicaSet=rs0"
    mongo_db: str = "history"
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"
    auth_jwks_url: str = "http://auth:8000/.well-known/jwks.json"


settings = Settings()
