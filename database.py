import asyncio
from xml.dom.minidom import DocumentType
from motor.motor_asyncio import AsyncIOMotorClient

# MongoDB connection URL
MONGODB_URL = "mongodb+srv://***:***@***/?retryWrites=true&w=majority"

async def connect_to_database():
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client["fastapi_users_db"]
    return db

