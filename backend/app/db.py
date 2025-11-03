# db.py
import os
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/visionconnect")
client = AsyncIOMotorClient(MONGO_URI)
db = client.get_default_database()  # uses DB from URI or "visionconnect"
users_collection = db["users"]
devices_collection = db["camera"]
