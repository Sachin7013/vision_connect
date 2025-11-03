# db.py
import os
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = os.environ.get("MONGO_URL", "mongodb://localhost:27017/visionconnect")
client = AsyncIOMotorClient(MONGO_URI)
db = client["vision_connect"]
users_collection = db["users"]
devices_collection = db["camera"]
