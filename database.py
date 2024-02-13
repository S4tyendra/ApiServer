import asyncio
from xml.dom.minidom import DocumentType
from motor.motor_asyncio import AsyncIOMotorClient

# MongoDB connection URL
MONGODB_URL = "mongodb://localhost:27017"

async def connect_to_database():
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client["fastapi_users_db"]
    return db

