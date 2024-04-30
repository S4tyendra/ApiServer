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


class Email(BaseModel):
    email: str


class Verify(BaseModel):
    email: str
    otp: str


def generate_random_otp():
    import random
    return str(random.randint(100000, 999999))


@router.post("/login")
async def login(email: Email):
    if not is_valid_email(email.email, ["gmail.com", "iiitkota.ac.in", "devh.in", "satyendra.in"]):
        raise HTTPException(status_code=400, detail="Invalid email")
    db = await connect_to_database()
    user = await db.users.find_one({"email": email.email})
    if user is None:
        id = str(datetime.now().timestamp()).replace(".", "")
        otp = [{"otp": generate_random_otp(), "created_at": datetime.now().timestamp()}]
        await db.users.insert_one({"_id": id, "email": email.email, "otp": otp})
        send_otp(email.email, otp[0].get('otp'))
    else:
        otp: list = user["otp"]
        generated_otp = {"otp": generate_random_otp(
        ), "created_at": datetime.now().timestamp(), }
        otp.append(generated_otp)
        await db.users.update_one({"email": email.email}, {"$set": {"otp": otp}})
        send_otp(email.email, generated_otp.get('otp'))
    return {"message": "OTP sent"}


@router.post("/verify")
async def verify(response: Response, verify: Verify):
    db = await connect_to_database()
    user = await db.users.find_one({"email": verify.email})
    if user is None:
        raise HTTPException(status_code=400, detail="Invalid email")
    otps = user["otp"]
    otps.reverse()
    for i in range(len(otps)):
        if otps[i].get("otp") == verify.otp:
            if datetime.now().timestamp() - otps[i].get("created_at") > 300:
                raise HTTPException(status_code=400, detail="OTP expired")
            else:
                cookie = secrets.token_hex(32)
                await db.users.update_one({"email": verify.email}, {"$set": {"otp": []}})
                await db.sessions.insert_one(
                    {"_id": cookie, "email": verify.email, "created_at": datetime.now().timestamp()})
                response.set_cookie(key="_id-c", value=cookie, httponly=False, secure=False)
                return {"message": "OTP verified", "cookie": cookie}

    raise HTTPException(status_code=400, detail="Invalid OTP")


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
        raise HTTPException(status_code=401, detail="Unauthorized")
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