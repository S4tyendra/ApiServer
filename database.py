from motor.motor_asyncio import AsyncIOMotorClient

# MongoDB connection URL
MONGODB_URL = "mongodb+srv://***:***@***.cbvk0so.mongodb.net/?retryWrites=true&w=majority&appName=devh"


# "mongodb+srv://***:***@***/?retryWrites=true&w=majority"
NOTES_DB_URL="mongodb+srv://mongodb:***@mongodbdevh.9fqlqam.mongodb.net/?retryWrites=true&w=majority&appName=mongodbdevh"

async def connect_to_database():
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client["fastapi_users_db"]
    return db

async def connect_to_notes_database():
    client = AsyncIOMotorClient(NOTES_DB_URL)
    db = client["notes"]
    return db
