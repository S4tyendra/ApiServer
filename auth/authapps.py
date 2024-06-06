from database import connect_to_database
from fastapi import APIRouter, HTTPException


async def getApp(app_id):
    db = await connect_to_database()
    app = await db.apps.find_one({"app_url": app_id})
    return app


router = APIRouter()


@router.get("/app")
async def app(appurl: str):
    db = await connect_to_database()
    app = await db.apps.find_one({"app_url": appurl})
    if app is None:
        raise HTTPException(status_code=400, detail="App not found")
    return app
