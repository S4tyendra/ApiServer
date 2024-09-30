from fastapi import APIRouter, HTTPException, Request, Response, Depends
from functions.db import get_database
from fastapi.responses import JSONResponse
from typing import Optional
from pydantic import BaseModel

router = APIRouter()

class UserProfile(BaseModel):
    _id: str
    email: str
    name: str
    picture: Optional[str]
    tokens: Optional[int]
    ai_auth: Optional[bool]
    is_private: Optional[bool]
    followers: Optional[list]

async def get_user_from_token(request: Request):
    cookie = request.cookies.get("_id-c")
    api_key = request.headers.get("X-API-KEY")
    auth_token = cookie or api_key

    db = await get_database()
    user_data = await db.sessions.find_one({"_id": auth_token})

    if user_data is None:
        raise HTTPException(status_code=401, detail="Invalid authentication")

    return user_data.get("email")

@router.get("/profile", response_model=UserProfile)
async def profile(request: Request, _id: str, requester_email: str = Depends(get_user_from_token)):
    db = await get_database()
    responser_data = await db.users.find_one({"_id": _id})

    if responser_data is None:
        raise HTTPException(status_code=404, detail="User not found")

    if responser_data.get("email") == requester_email:
        return UserProfile(**responser_data)

    if responser_data.get("is_private", False):
        if requester_email not in responser_data.get("followers", []):
            raise HTTPException(status_code=403, detail="Private user")

    return UserProfile(**responser_data)

@router.get("/me", response_model=UserProfile)
async def me(requester_email: str = Depends(get_user_from_token)):
    db = await get_database()

    projection = ["_id", "email", "name", "picture", "tokens", "ai_auth"]

    if requester_email.endswith("@iiitkota.ac.in"):
        user_data = await db.users.find_one({"email": requester_email}, projection=projection)
        if user_data is None:
            raise HTTPException(status_code=404, detail="User not found")
        user_data["ai_auth"] = user_data.get("ai_auth", False)
    else:
        user_data = await db.users.find_one({"email": requester_email}, projection=projection[:-1])
        if user_data is None:
            raise HTTPException(status_code=404, detail="User not found")

    return UserProfile(**user_data)