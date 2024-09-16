from database import connect_to_database
from auth.authapps import getApp_by_id
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

local = bool(os.getenv("LOCAL", False))


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
        app_ = await getApp_by_id(app_id)
        if not app_:
            return HTTPException(404, "App not found")
        email = app_.get("email", None)
        print(app_email or email)
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        # include_granted_scopes="true",
        hd=app_email or email,  # "iiitkota.ac.in",
        # prompt="consent",
        enable_incremental_authorization=True,
    )
    app_map[state] = app_
    print(authorization_url)
    return RedirectResponse(authorization_url)


@router.get("/googlesignin")
async def callback(request: Request, response: Response):
    state = request.query_params.get("state")
    redirect_uri = (
        "http://localhost:8000/auth/googlesignin"
        if local
        else "https://aws-api.devh.in/auth/googlesignin"
    )
    if state in app_map.keys():
        redirect_uri = redirect_uri
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE, scopes=SCOPES, state=state, redirect_uri=redirect_uri
        )

        flow.fetch_token(
            authorization_response=str(request.url).replace("http", "https")
        )

        id_token_data = google_id_token.verify_oauth2_token(
            flow.credentials.id_token, requests.Request()
        )

        email = id_token_data["email"]
        name = id_token_data["name"]
        picture = id_token_data["picture"]

        db = await connect_to_database()
        user = await db.users.find_one({"email": email})
        cookie = secrets.token_hex(32)

        if user is None:
            print(f"User not found, creating new user, {email}")
            id = str(datetime.now().timestamp()).replace(".", "")
            await db.users.insert_one(
                {"_id": id, "email": email, "name": name, "picture": picture}
            )
        user = await db.users.find_one({"email": email})
        id = user["_id"]
        app = app_map.get(state)
        if app:
            await db.sessions.insert_one(
                {
                    "_id": cookie,
                    "email": user.get("email"),
                    "created_at": datetime.now().timestamp(),
                    "type": app.get("_id"),
                }
            )
            response.set_cookie(key="_id-c", value=cookie, httponly=False, secure=False)
            return RedirectResponse(f"{app.get('redirect_url')}?token={cookie}")
        else:
            await db.sessions.insert_one(
                {
                    "_id": cookie,
                    "email": user.get("email"),
                    "created_at": datetime.now().timestamp(),
                    "type": "WEB-KEY",
                }
            )
            response.set_cookie(key="_id-c", value=cookie, httponly=False, secure=False)
            return RedirectResponse("https://account.devh.in/auth?_id-c=" + cookie)
