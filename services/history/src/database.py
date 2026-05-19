from motor.motor_asyncio import AsyncIOMotorClient

from src.settings import settings

client = AsyncIOMotorClient(settings.mongo_url, tz_aware=True)
db = client[settings.mongo_db]
history_collection = db.get_collection("transactions")