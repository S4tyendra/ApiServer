import secrets
from datetime import datetime

from fastapi import APIRouter, Form, HTTPException, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
from starlette.requests import Request

from database import connect_to_database
from functions.email_funcs import is_valid_email, send_otp
import html  # For HTML escaping
router = APIRouter()



@router.get("/logout")
async def logout(response: Response, request: Request, all_sessions: bool = False):
    cookie = request.cookies.get("_id-c")
    if cookie is not None:
        if all_sessions:
            db = await connect_to_database()
            data = await db.sessions.find_one({"_id": cookie})
            await db.sessions.delete_many({"email": data.get("email")})
        else:
            db = await connect_to_database()
            await db.sessions.delete_one({"_id": cookie})
    response.delete_cookie(key="_id-c")
    return RedirectResponse(url="/")


@router.get("/createapikey")
async def create_api_key(request: Request):
    db = await connect_to_database()
    cookie = request.cookies.get("_id-c")
    if cookie is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    user = await db.sessions.find_one({"_id": cookie})
    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Count the number of existing API keys for the user
    api_keys_count = await db.sessions.count_documents({"email": user.get("email"), "type": "api_key"})
    if api_keys_count >= 10:
        raise HTTPException(status_code=400, detail="Maximum number of API keys reached")

    api_key = secrets.token_hex(32)
    await db.sessions.insert_one(
        {"_id": api_key, "email": user.get("email"), "created_at": datetime.now().timestamp(), "type": "api_key"})
    return {"api_key": api_key}


@router.get("/deleteapikeys")
async def delete_api_key(request: Request):
    db = await connect_to_database()
    cookie = request.cookies.get("_id-c")
    if cookie is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    cookie_user = await db.sessions.find_one({"_id": cookie})
    if cookie_user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    await db.sessions.delete_many({"email": cookie_user.get("email"), "type": "api_key"})
    return {"message": "All API keys deleted"}


@router.get("/listapikeys")
async def list_api_keys(request: Request):
    db = await connect_to_database()
    cookie = request.cookies.get("_id-c")
    if cookie is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    cookie_user = await db.sessions.find_one({"_id": cookie})
    if cookie_user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    email = cookie_user.get("email")
    api_keys_cursor = db.sessions.find({"email": email, "type": "api_key"})
    api_keys = []
    async for i in api_keys_cursor:
        api_keys.append(i["_id"][:4] + '*' * (len(i["_id"]) - 4))
    return {"api_keys": api_keys}



@router.get("/tokens")
async def get_tokens(request: Request):
    db = await connect_to_database()
    cookie = request.cookies.get("_id-c")
    if cookie is None:
        raise HTTPException(status_code=401, detail="Unauthorized, Please login first")
    cookie_user = await db.sessions.find_one({"_id": cookie})
    if cookie_user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    email = cookie_user.get("email")
    user = await db.users.find_one({"email": email})
    tokens = user.get("tokens", None)
    if tokens is None:
        await db.users.update_one({"email": email}, {"$set": {"tokens": 100}})
        tokens = 100
    return {"tokens": tokens}