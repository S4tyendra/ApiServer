import os
import secrets
import logging
from datetime import datetime
from typing import Optional
from urllib.parse import urlencode, urlparse

from fastapi import APIRouter, Request, HTTPException, Response
from fastapi.responses import RedirectResponse
from google.auth.transport import requests
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token as google_id_token
from dotenv import load_dotenv

from functions.db import get_database

# Load environment variables
load_dotenv(".env")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI router
router = APIRouter()

# Constants
CLIENT_SECRETS_FILE = "auth/clientsecret.json"
SCOPES = [
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "openid",
]
REDIRECT_URI = "https://aws-api.devh.in/auth/googlesignin"
COOKIE_NAME = "_id-c"
SESSION_EXPIRY = 3600  # 1 hour

# For development only. Remove in production.
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

# Allowed redirect domains
ALLOWED_REDIRECT_DOMAINS = {"account.devh.in"}


def is_valid_redirect_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.netloc in ALLOWED_REDIRECT_DOMAINS


@router.get("/login")
async def login(request: Request, domain: Optional[str] = None, redirect_uri: Optional[str] = None):
    logger.info(f"Login attempt for domain: {domain}")

    if redirect_uri and not is_valid_redirect_url(redirect_uri):
        raise HTTPException(status_code=400, detail="Invalid redirect URI")

    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )

    # Generate a unique state
    state = secrets.token_urlsafe(16)

    authorization_url, _ = flow.authorization_url(
        access_type="offline",
        hd=domain,  # This restricts sign-in to the specified domain
        prompt="select_account",  # Forces account selection even if already logged in
        state=state,
        enable_incremental_authorization=True,
    )

    # Store state and redirect_uri in the database
    db = await get_database()
    await db.oauth_states.insert_one({
        "state": state,
        "redirect_uri": redirect_uri,
        "created_at": datetime.now().timestamp(),
    })

    return RedirectResponse(authorization_url)


@router.get("/googlesignin")
async def callback(request: Request, response: Response, state: str):
    if not state:
        logger.warning("No state parameter found")
        raise HTTPException(status_code=400, detail="Invalid state. Please try logging in again.")

    # Retrieve and delete the state from the database
    db = await get_database()
    state_data = await db.oauth_states.find_one_and_delete({"state": state})

    if not state_data:
        logger.warning(f"Invalid state: {state}")
        raise HTTPException(status_code=400, detail="Invalid state. Please try logging in again.")

    redirect_uri = state_data.get("redirect_uri")

    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, state=state, redirect_uri=REDIRECT_URI
    )

    try:
        flow.fetch_token(authorization_response=str(request.url).replace("http", "https"))
        id_token_data = google_id_token.verify_oauth2_token(
            flow.credentials.id_token, requests.Request()
        )
    except Exception as e:
        logger.error(f"Failed to authenticate: {str(e)}")
        raise HTTPException(status_code=400, detail="Failed to authenticate. Please try again.")

    email = id_token_data["email"]
    name = id_token_data["name"]
    picture = id_token_data["picture"]

    user = await db.users.find_one({"email": email})
    cookie = secrets.token_hex(32)

    if user is None:
        id = str(datetime.now().timestamp()).replace(".", "")
        await db.users.insert_one(
            {"_id": id, "email": email, "name": name, "picture": picture}
        )
    user = await db.users.find_one({"email": email})

    session_data = {
        "_id": cookie,
        "email": user.get("email"),
        "created_at": datetime.now().timestamp(),
        "type": "WEB-KEY",
    }
    await db.sessions.insert_one(session_data)

    response.set_cookie(
        key=COOKIE_NAME,
        value=cookie,
        httponly=True,
        secure=True,
        domain=".devh.in",
        max_age=SESSION_EXPIRY,
        samesite="lax"
    )

    logger.info(f"User logged in successfully. Email: {email}")

    # Use the original redirect_uri if provided and valid, otherwise use a default
    final_redirect = redirect_uri if redirect_uri and is_valid_redirect_url(
        redirect_uri) else "https://account.devh.in/auth"
    return RedirectResponse(f"{final_redirect}?_id-c={cookie}")