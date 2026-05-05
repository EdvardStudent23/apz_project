from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "core_banking"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/core_banking"
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"
    auth_jwks_url: str = "http://localhost:8001/.well-known/jwks.json"


settings = Settings()
