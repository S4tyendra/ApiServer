from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from database import Database

db = Database()

async def db_connect() ->  AsyncIOMotorClient:
    return await db.connect()
async def db_close() -> None:
    return await db.close()
async def get_database(db_name="fastapi_users_db") -> AsyncIOMotorDatabase:
    return await db.get_db(db_name)