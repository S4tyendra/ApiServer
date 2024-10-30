from fastapi import APIRouter, HTTPException, Request, Response, Depends
from typing import List, Dict, Any
from functions.apiwrapper import get_user
from functions.db import get_database

router = APIRouter()


@router.get("/detail")
async def get_app_detail(request: Request, response: Response, app:str):
    user = await get_user(request, accept=["WEB-KEY"])
    db = await get_database()
    sessions = db.sessions.find({"email": user.get("email"),"type":app})
    app_detail = await db.apps.find_one({"_id":app})
    if not app_detail:
        response.status_code = 404
        raise HTTPException(status_code=404, detail="App not found")
    sessions_tr = []
    async for session in sessions:
        sessions_tr.append(session)
    return {"sessions": sessions_tr, "user_email":user.get('email'), **app_detail}
