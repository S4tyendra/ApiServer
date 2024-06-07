import os
import secrets
from datetime import datetime

from dotenv import load_dotenv
from fastapi import APIRouter, Request, HTTPException, Response
from fastapi.responses import RedirectResponse
from google.auth.transport import requests
from google.oauth2 import id_token as google_id_token
from google_auth_oauthlib.flow import Flow

load_dotenv(".env")

local = bool(os.getenv("LOCAL", False))

from auth.authapps import getApp
from database import connect_to_database

router = APIRouter()
CLIENT_SECRETS_FILE = "auth/clientsecret.json"
SCOPES = [
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "openid",
]

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

app_map = []


@router.get("/googlelogin")
async def login():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=(
            "http://localhost:8000/auth/googlesignin"
            if local
            else "https://aws-api.devh.in/auth/googlesignin"
        )
    )
    authorization_url, state = flow.authorization_url(
        access_type="offline", include_granted_scopes="true",prompt="select_account"
    )
    app_map.append(state)
    return RedirectResponse(authorization_url)


@router.get("/googlesignin")
async def callback(request: Request, response: Response):
    state = request.query_params.get("state")
    redirect_uri = (
        "http://localhost:8000/auth/googlesignin"
        if local
        else "https://aws-api.devh.in/auth/googlesignin"
    )
    if state in app_map:
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
        print(id_token_data)

        email = id_token_data["email"]

        db = await connect_to_database()
        user = await db.users.find_one({"email": email})
        cookie = secrets.token_hex(32)

        if user is None:
            id = str(datetime.now().timestamp()).replace(".", "")
            await db.users.insert_one(
                {"_id": id, **id_token_data}
            )
        await db.sessions.insert_one({"_id": cookie, "email": email})
        return RedirectResponse("https://account.devh.in/auth?_id-c=" + cookie)
