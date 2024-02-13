import time

from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader
from starlette.requests import Request

from database import connect_to_database

API_KEY_NAME = "X-API-KEY"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


async def api_key_auth(api_key: str = Depends(api_key_header)):
    if api_key is None:
        raise HTTPException(status_code=401, detail="Unauthorized, api key required")
    db = await connect_to_database()
    user = await db.sessions.find_one({"_id": api_key, "type": "api_key"})
    email = user['email']
    await db.users.update_one({"email": email}, {"$set":
                                                     {"last_accessed": time.time()}
                                                 })
    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorized, api key required")
    return user
