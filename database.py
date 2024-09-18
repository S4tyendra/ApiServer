from motor.motor_asyncio import AsyncIOMotorClient

# MongoDB connection URL
MONGODB_URL = "mongodb+srv://s4tyendra:satya@devh.cbvk0so.mongodb.net/?retryWrites=true&w=majority&appName=devh"

# "mongodb+srv://satya:satya@satyavercel.vkbon8d.mongodb.net/?retryWrites=true&w=majority"
NOTES_DB_URL = MONGODB_URL


# "mongodb+srv://mongodb:satyendra@mongodbdevh.9fqlqam.mongodb.net/?retryWrites=true&w=majority&appName=mongodbdevh"


async def connect_to_database(db_name="fastapi_users_db"):
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[db_name]
    return db


async def connect_to_notes_database():
    client = AsyncIOMotorClient(NOTES_DB_URL)
    db = client["notes"]
    return db
