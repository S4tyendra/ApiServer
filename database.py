from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
# MongoDB connection URL
MONGODB_URL = "mongodb+srv://***:***@***.cbvk0so.mongodb.net/?retryWrites=true&w=majority&appName=devh"

# "mongodb+srv://***:***@***/?retryWrites=true&w=majority"
NOTES_DB_URL = MONGODB_URL


# "mongodb+srv://mongodb:***@mongodbdevh.9fqlqam.mongodb.net/?retryWrites=true&w=majority&appName=mongodbdevh"


from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional


class Database:
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None

    async def connect(self) -> AsyncIOMotorClient:
        if self.client is None:
            self.client = AsyncIOMotorClient(MONGODB_URL)
        return self.client

    async def close(self) -> None:
        if self.client is not None:
            self.client.close()
            self.client = None

    async def get_db(self, database: str = "fastapi_users_db") -> AsyncIOMotorDatabase:
        if self.client is None:
            await self.connect()
        return self.client[database]
