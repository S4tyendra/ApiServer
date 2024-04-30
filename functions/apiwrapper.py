import time
from fastapi import Depends, HTTPException, Response
from fastapi.security import APIKeyHeader
from starlette.requests import Request
from database import connect_to_database

API_KEY_NAME = "X-API-KEY"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False, scheme_name="API Key", description="API Key for authentication")


async def api_key_auth(request:Request, call_next,  api_key: str = Depends(api_key_header), ):
    if api_key is None:
        raise HTTPException(status_code=401, detail="Unauthorized, api key required")
    db = await connect_to_database()
    user = await db.sessions.find_one({"_id": api_key, "type": "api_key"})
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized, api key invalid")
    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorized, api key required")
    
    email = user['email']
    user_in_db = await db.users.find_one({"email": email})
    tokens = user_in_db.get("tokens", None)
    if tokens is None:
        await db.users.update_one({"email": email}, {"$set":
                                                    {"tokens": 100,}
                                                 })
        tokens = 100
    if tokens <= 0:
        raise HTTPException(status_code=401, detail="Unauthorized, no tokens left")
    
    path = request.url.path
    print(path)
    tc = None
    if path.endswith("generate") or path.endswith("sendpdf"):
        tc = 2
    await db.users.update_one({"email": email}, {"$set":
                                                        {"last_accessed": time.time()},
                                                        "$inc": {"tokens": tc or 1}
                                                    })
        
async def tokenconsuption(api_key, tokens):
    db = await connect_to_database()
    user = await db.sessions.find_one({"_id": api_key, "type": "api_key"})
    email = user['email']
    user_in_db = await db.users.find_one({"email": email})
    tokens = user_in_db.get("tokens", None)
    if tokens is None:
        await db.users.update_one({"email": email}, {"$set":
                                                    {"tokens": 100,}
                                                 })
        return
    await db.users.update_one({"email": email}, {"$set":
                                                        {"last_accessed": time.time()},
                                                        "$inc": {"tokens": tokens}
                                                    })
        
