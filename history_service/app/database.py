from motor.motor_asyncio import AsyncIOMotorClient
import os

MONGODB_URL = "mongodb://mongo1:27017,mongo2:27018,mongo3:27019/?replicaSet=rs0"

client = AsyncIOMotorClient(MONGODB_URL)
db = client.nanobank_history 
history_collection = db.get_collection("transactions")