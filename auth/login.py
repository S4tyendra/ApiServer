import secrets
from fastapi import APIRouter, Request, Response, HTTPException, Depends
from functions.db import get_database
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter()

async def get_db():
    return await get_database()


@router.get("/tokens")
async def get_tokens(
        request: Request,
        db: AsyncIOMotorDatabase = Depends(get_db)
):
    api_key = request.headers.get("X-API-KEY")
    if not api_key:
        raise HTTPException(status_code=401, detail="API key not provided")

    session_user = await db.sessions.find_one({"_id": api_key})
    if not session_user:
        raise HTTPException(status_code=401, detail="Invalid API key")

    email = session_user.get("email")
    user = await db.users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    tokens = user.get("tokens", 10)
    if "tokens" not in user:
        await db.users.update_one({"email": email}, {"$set": {"tokens": tokens}})

    return {"tokens": tokens}