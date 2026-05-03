from __future__ import annotations

from neo4j import AsyncDriver, AsyncGraphDatabase

from src.settings import settings


def make_driver() -> AsyncDriver:
    return AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )
