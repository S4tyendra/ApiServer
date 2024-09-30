from functions.db import get_database
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

async def get_app(app_id: str) -> Optional[dict]:
    db: AsyncIOMotorDatabase = await get_database()
    return await db.apps.find_one({"app_url": app_id})

async def get_app_by_id(app_id: str) -> Optional[dict]:
    db: AsyncIOMotorDatabase = await get_database()
    return await db.apps.find_one({"_id": app_id})