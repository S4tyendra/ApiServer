import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Request, Response, Depends
from functions.apiwrapper import get_user
from functions.db import get_database

router = APIRouter()


@router.get("/approve")
async def approve_an_app(request: Request, response: Response, app: str):
    user = await get_user(request, accept=["WEB-KEY"])
    db = await get_database()

    # Check if app exists
    app_detail = await db.apps.find_one({"_id": app})
    if not app_detail:
        response.status_code = 404
        raise HTTPException(status_code=404, detail="App not found")

    app_name = app_detail.get("_id")
    if not app_name:
        response.status_code = 404
        raise HTTPException(status_code=404, detail="App not found")

    # Calculate the start of the current day in timestamp
    now = datetime.now()
    start_of_day = datetime(now.year, now.month, now.day).timestamp()
    end_of_day = (datetime(now.year, now.month, now.day) + timedelta(days=1)).timestamp()

    # Count today's approvals for this user and app
    daily_approvals = await db.sessions.count_documents({
        "email": user.get("email"),
        "type": app_name,
        "created_at": {
            "$gte": start_of_day,
            "$lt": end_of_day
        }
    })

    # Check if user has reached daily limit
    if daily_approvals >= 2:
        response.status_code = 429
        raise HTTPException(
            status_code=429,
            detail="You can only approve 2 times per day. Please try again tomorrow, or use any old sessions."
        )

    # Create new session
    session_id = secrets.token_hex(32)
    await db.sessions.insert_one({
        "_id": session_id,
        "email": user.get("email"),
        "type": app_name,
        "created_at": now.timestamp()
    })

    return {"token": session_id}