from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.settings import settings


class Base(DeclarativeBase):
    pass


def make_engine() -> AsyncEngine:
    return create_async_engine(
        settings.database_url,
        future=True,
        pool_size=20,
        max_overflow=10,
    )


def make_session_factory(engine: AsyncEngine) -> async_sessionmaker:
    return async_sessionmaker(engine, expire_on_commit=False)
