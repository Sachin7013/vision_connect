# db.py - CORRECTED VERSION
import os
from motor.motor_asyncio import AsyncIOMotorClient

# Read from MONGODB_URL (matching what's in Render)
MONGO_URI = os.environ.get("MONGODB_URL", "mongodb://localhost:27017/vision_connect")

# Create async client
client = AsyncIOMotorClient(MONGO_URI)

# Access the database
db = client["vision_connect"]

# Collections
users_collection = db["users"]
devices_collection = db["camera"]
