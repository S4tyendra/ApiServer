from fastapi import APIRouter, Request, Response, Depends
from typing import List, Dict, Any
from functions.apiwrapper import get_user
from functions.db import get_database

router = APIRouter()


@router.get("/list")
async def get_apps_list(request: Request, response: Response):
    """
    Returns: List of apps available based on the user's email.
    """
    user = await get_user(request, accept=["WEB-KEY"])
    db = await get_database()
    cursor = db.apps.find({})
    all_apps = await cursor.to_list(length=None)

    user_email = user.get('email', '').split('@')[-1].lower()  # Get domain part of email

    filtered_apps = []
    for app in all_apps:
        app_email = app.get('email', '').lower()
        if not app_email or app_email == user_email:
            filtered_apps.append(app)

    return filtered_apps