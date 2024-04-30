import asyncio
from xml.dom.minidom import DocumentType
from motor.motor_asyncio import AsyncIOMotorClient

# MongoDB connection URL
MONGODB_URL ="mongodb+srv://s4tyendra:satya@devh.cbvk0so.mongodb.net/?retryWrites=true&w=majority&appName=devh" # "mongodb+srv://satya:satya@satyavercel.vkbon8d.mongodb.net/?retryWrites=true&w=majority"

async def world_db():
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client["WorldDB"]
    return db

