from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "history"
    mongo_url: str = "mongodb://mongo_1:27017,mongo_2:27017,mongo_3:27017/?replicaSet=rs0"
    mongo_db: str = "history"
    rabbitmq_url: str = "amqp://rabbit:rabbit@rabbitmq:5672/"
    auth_jwks_url: str = "http://auth_1:8001/.well-known/jwks.json"


settings = Settings()
