from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from src.settings import settings


def make_client() -> AsyncIOMotorClient:
    return AsyncIOMotorClient(settings.mongo_url, w="majority")


def make_database(client: AsyncIOMotorClient) -> AsyncIOMotorDatabase:
    return client[settings.mongo_db]
