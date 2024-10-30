import secrets
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request, Response, Depends
from functions.apiwrapper import get_user
from functions.db import get_database

router = APIRouter()


@router.get("/approve")
async def approve_an_app(request: Request, response: Response, app:str):
    user = await get_user(request, accept=["WEB-KEY"])
    db = await get_database()
    app_detail = await db.apps.find_one({"_id": app})
    if not app_detail:
        response.status_code = 404
        raise HTTPException(status_code=404, detail="App not found")
    app_name = app_detail.get("_id")
    if not app_name:
        response.status_code = 404
        raise HTTPException(status_code=404, detail="App not found")
    session_id = secrets.token_hex(32)
    db.sessions.insert_one({
        "_id": session_id,
        "email": user.get("email"),
        "type": app_name,
        "created_at": datetime.now().timestamp()
    })

    return {"token": session_id}
