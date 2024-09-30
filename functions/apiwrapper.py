import time
from typing import Optional, List

from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader
from starlette.requests import Request

from functions.db import get_database

API_KEY_NAME = "X-API-KEY"
api_key_header = APIKeyHeader(
    name=API_KEY_NAME,
    auto_error=False,
    scheme_name="API Key",
    description="API Key for authentication",
)

import icecream
from icecream import ic

async def get_user(
        accept: List[str],
        request: Request,
        tokens: Optional[int] = None,
):
    api_key = request.headers.get(API_KEY_NAME)

    if not api_key:
        print("No api key")
        raise HTTPException(status_code=401, detail="Unauthorized, api key required")

    db = await get_database()
    accept_ = [str(i) for i in accept if i]

    ic(accept_)
    api_key = str(api_key)

    session = await db.sessions.find_one({"_id": api_key, "type": {"$in": accept_}})
    if not session:
        raise HTTPException(status_code=401, detail="Unauthorized, invalid session")

    user = await db.users.find_one({"email": session.get('email')})
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized, user not found")

    current_tokens = user.get("tokens", 10)  # Default to 10 if not set

    icecream.ic(current_tokens)

    if tokens is not None:
        token_cost = tokens
        if current_tokens + token_cost < 0:
            raise HTTPException(status_code=401, detail="Not enough Tokens")

        await db.users.update_one(
            {"email": user['email']},
            {
                "$set": {
                    "last_accessed": time.time(),
                    "tokens": current_tokens + token_cost
                }
            }
        )
    else:
        await db.users.update_one(
            {"email": user['email']},
            {"$set": {"last_accessed": time.time()}}
        )

    return user

async def refund_tokens(email: str, tokens_to_refund: int):
    db = await get_database()

    try:
        result = await db.users.update_one(
            {"email": email},
            {"$inc": {"tokens": tokens_to_refund}}
        )

        if result.modified_count == 0:
            print(f"Warning: No user found with email {email} for token refund.")
            return False

        print(f"Successfully refunded {tokens_to_refund} tokens to user {email}")
        return True

    except Exception as e:
        print(f"Error refunding tokens to user {email}: {str(e)}")
        return False



# async def get_user(
#         request: Request,
#         accept: List[str],

# ):
#     api_key = request.headers.get(API_KEY_NAME)

#     if not api_key:
#         raise HTTPException(status_code=401, detail="Unauthorized, api key required")

#     db = await get_database()

#     session = await db.sessions.find_one({"_id": api_key, "type": {"$in": accept}})
#     if not session:
#         raise HTTPException(status_code=401, detail="Unauthorized, invalid session")

#     user = await db.users.find_one({"email": session.get('email')})
#     if not user:
#         raise HTTPException(status_code=401, detail="Unauthorized, user not found")
#     return user