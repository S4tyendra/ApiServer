import secrets
from fastapi import APIRouter, Request, Response, HTTPException, Depends
from functions.db import get_database
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter()

async def get_db():
    return await get_database()

@router.get("/approveapp")
async def approve_app(
        request: Request,
        response: Response,
        app_id: str,
        db: AsyncIOMotorDatabase = Depends(get_db)
):
    app = await db.apps.find_one({"_id": app_id})
    if not app:
        raise HTTPException(status_code=404, detail="App Not Found")

    token = request.headers.get("WEB-KEY")
    if not token:
        raise HTTPException(status_code=401, detail="Not Authorized")

    session = await db.sessions.find_one({"_id": token, "type": "WEB-KEY"})
    if not session:
        raise HTTPException(status_code=401, detail="Unauthorized")

    email = session.get("email")
    if not email:
        raise HTTPException(status_code=404, detail="User not found")

    new_token = secrets.token_hex(32)
    await db.sessions.insert_one(
        {"_id": new_token, "email": email, "type": f"{app['_id']}"}
    )

    return {"redirect": f"{app['redirect_url']}?token={new_token}"}

@router.get("/appdetails")
async def app_details(
        request: Request,
        response: Response,
        app_url: str,
        db: AsyncIOMotorDatabase = Depends(get_db)
):
    app = await db.apps.find_one({"app_url": app_url})
    if not app:
        raise HTTPException(status_code=404, detail="App not found")
    return app

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