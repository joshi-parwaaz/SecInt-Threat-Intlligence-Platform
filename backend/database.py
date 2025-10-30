"""
database.py - MongoDB connection and configuration
"""
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
import os

MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/secint")
DB_NAME = "secint"

client: AsyncIOMotorClient = None
db = None

async def connect_db():
    """Connect to MongoDB on startup"""
    global client, db
    try:
        client = AsyncIOMotorClient(MONGO_URI)
        db = client[DB_NAME]
        # Test connection
        await client.admin.command('ping')
        print(f"✅ Connected to MongoDB at {MONGO_URI}")
    except ConnectionFailure as e:
        print(f"❌ MongoDB connection failed: {e}")
        raise

async def disconnect_db():
    """Disconnect from MongoDB on shutdown"""
    global client
    if client:
        client.close()
        print("✅ Disconnected from MongoDB")

def get_database():
    """Get database instance"""
    return db

def get_collection(name: str):
    """Get a specific collection"""
    return db[name]
