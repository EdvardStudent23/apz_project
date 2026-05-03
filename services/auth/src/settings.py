from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "auth"
    database_url: str = "postgresql+asyncpg://localhost/auth"
    redis_url: str = "redis://localhost:6379/0"

    jwt_algorithm: str = "RS256"
    jwt_private_key_path: str = "/run/secrets/auth_jwt_private.pem"
    jwt_public_key_path: str = "/run/secrets/auth_jwt_public.pem"
    jwt_kid: str = "auth-key-1"
    jwt_issuer: str = "auth"
    jwt_ttl_seconds: int = 3600


settings = Settings()
