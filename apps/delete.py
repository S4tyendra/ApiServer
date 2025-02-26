from fastapi import APIRouter, HTTPException, Request, Response, Depends
from functions.apiwrapper import get_user
from functions.db import get_database

router = APIRouter()


@router.delete("/session")
async def delete_app_session(request: Request, response: Response, app:str, session:str):
    user = await get_user(request, accept=["WEB-KEY"])
    db = await get_database()
    sessions = db.sessions.find({"email": user.get("email"),"type":app, "_id":session})
    if not sessions:
        response.status_code = 404
        raise HTTPException(status_code=404, detail="Session not found")
    app_detail = await db.apps.find_one({"_id":app})
    if not app_detail:
        response.status_code = 404
        raise HTTPException(status_code=404, detail="App not found")

    await db.sessions.delete_one({"email": user.get("email"),"type":app, "_id":session})
    return {"status":"deleted"}

