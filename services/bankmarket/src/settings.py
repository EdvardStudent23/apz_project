from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "bankmarket"
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "neo4j"
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"
    core_banking_url: str = "http://core_banking:8000"
    auth_jwks_url: str = "http://auth:8000/.well-known/jwks.json"


settings = Settings()
