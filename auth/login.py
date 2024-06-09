import secrets

from fastapi import APIRouter, Request, Response, HTTPException
from fastapi.responses import RedirectResponse

from database import connect_to_database

router = APIRouter()


@router.get("/approveapp")
async def approve_app(request: Request, response: Response, app_id: str):
    db = await connect_to_database()
    app = await db.apps.find_one({"_id": app_id})

    if not app:
        raise HTTPException(status_code=400, detail="App Not Found")

    token = request.headers.get("WEB-KEY")
    if not token:
        raise HTTPException(status_code = 401, detail="Not Authorized")

    sessn = await db.sessions.find_one({"_id": token})
    if not sessn:
        raise HTTPException(status_code=401, detail="Unauthorized")

    email = sessn.get("email")
    if not email:
        raise HTTPException(status_code=404, detail="User not found")

    new_token = secrets.token_hex(32)
    await db.sessions.insert_one({"_id": new_token, "email": email, "type": f"{app.get('_id')}"})

    return {'redirect': f"{app.get('redirect_url')}?token={new_token}"}


@router.get("/appdetails")
async def app_details(request: Request, response: Response, app_url: str):
    db = await connect_to_database()
    app = await db.apps.find_one({"app_url": app_url})
    if app:
        return app
    return HTTPException(status_code=400, detail="App not found")

@router.get("/tokens"):
async def get_tokens(request:Request):
    
    api_key = request.headers.get('X-API-KEY')
    if api_key:
        db = await connect_to_database()
        session_user = await db.sessions.find_one({"_id": token})
        if session_user:
            email = session_user.get('email')
            user = await db.users.find_one({'email':email})
            if user:
                tokens = user.get('tokens')
                if tokens:
                    return {'tokens':tokens}
                else:
                    await db.users.find_one({'email':email},{'tokens':10})
                    return {'tokens':tokens}
