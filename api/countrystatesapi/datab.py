from motor.motor_asyncio import AsyncIOMotorClient

# MongoDB connection URL
MONGODB_URL = "mongodb+srv://***:***@***.cbvk0so.mongodb.net/?retryWrites=true&w=majority&appName=devh"  # "mongodb+srv://***:***@***/?retryWrites=true&w=majority"


async def world_db():
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client["WorldDB"]
    return db
TOKEN = 1