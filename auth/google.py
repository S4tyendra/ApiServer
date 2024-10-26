from pytz import timezone

from functions.add_to_logs import add_to_logs
from functions.db import get_database
from auth.authapps import get_app_by_id
import os
import secrets
from fastapi import APIRouter, Request, HTTPException, Response
from fastapi.responses import RedirectResponse
from google.auth.transport import requests
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token as google_id_token
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(".env")

local = os.getenv("LOCAL", "False").lower() == "true"

router = APIRouter()
CLIENT_SECRETS_FILE = "auth/clientsecret.json"
SCOPES = [
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "openid",
]

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

app_map = {}

@router.get("/googlelogin")
async def login(app_id=None, app_email=None):
    app_ = None

    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=(
            "http://localhost:8000/auth/googlesignin"
            if local
            else "https://aws-api.devh.in/auth/googlesignin"
        ),
    )
    email = None
    if app_id and not app_email:
        app_ = await get_app_by_id(app_id)
        if not app_:
            raise HTTPException(status_code=404, detail="App not found")
        email = app_.get("email", None)

    authorization_url, state = flow.authorization_url(
        access_type="offline",
        hd=app_email or email,
        enable_incremental_authorization=True,
    )
    app_map[state] = app_
    return RedirectResponse(authorization_url)

@router.get("/googlesignin")
async def callback(request: Request, response: Response):
    state = request.query_params.get("state")
    redirect_uri = (
        "http://localhost:8000/auth/googlesignin"
        if local
        else "https://aws-api.devh.in/auth/googlesignin"
    )
    if state not in app_map:
        raise HTTPException(status_code=400, detail="Invalid state parameter, Goback and login again!")

    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, state=state, redirect_uri=redirect_uri
    )

    try:
        flow.fetch_token(authorization_response=str(request.url).replace("http", "https"))
        id_token_data = google_id_token.verify_oauth2_token(
            flow.credentials.id_token, requests.Request()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to authenticate: {str(e)}")

    email = id_token_data["email"]
    name = id_token_data["name"]
    picture = id_token_data["picture"]

    db = await get_database()
    user = await db.users.find_one({"email": email})
    cookie = secrets.token_hex(32)

    if user is None:
        id = str(datetime.now().timestamp()).replace(".", "")
        await db.users.insert_one(
            {"_id": id, "email": email, "name": name, "picture": picture}
        )
    user = await db.users.find_one({"email": email})
    id = user["_id"]
    app = app_map.get(state)

    session_data = {
        "_id": cookie,
        "email": user.get("email"),
        "created_at": datetime.now().timestamp(),
        "type": app.get("_id") if app else "WEB-KEY",
    }
    await db.sessions.insert_one(session_data)

    response.set_cookie(key="_id-c", value=cookie, httponly=True, secure=not local)
    del app_map[state]
    await add_to_logs(
        session=cookie,
        email=email,
        message="Logged in",
        app=app.get("_id") if app else "WEB-KEY",
        timestamp=datetime.now(tz=timezone('Asia/Kolkata')).timestamp(),
    )
    if app:
        return RedirectResponse(f"{app.get('redirect_url')}?token={cookie}")
    else:
        return RedirectResponse(f"https://account.devh.in/auth?_id-c={cookie}")

    # Clean up the app_map

