import os
import logging
from typing import Optional
from fastapi import APIRouter, Request, HTTPException, Response
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
import httpx
from functions.db import get_database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

CLIENT_SECRETS_FILE = os.getenv("CLIENT_SECRETS_FILE", "iiitkres/clientsecret.json")
SCOPES = [
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/generative-language.retriever",
    "openid",
]
REDIRECT_URI = "https://api.devh.in/iiitk/auth"

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

def create_flow():
    try:
        return Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE,
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI,
        )
    except Exception as e:
        logger.error(f"Error creating flow: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/auth")
async def auth(
        request: Request,
        response: Response,
        state: Optional[str] = None,
        code: Optional[str] = None,
        token: Optional[str] = None,
):
    db = await get_database()

    if not state and not code:
        return await handle_initial_auth(db, token)
    elif state and code:
        return await handle_callback(db, state, code)
    else:
        raise HTTPException(status_code=400, detail="Invalid request")

async def handle_initial_auth(db, token):
    if not token:
        raise HTTPException(status_code=400, detail="Token not provided")

    session = await db.sessions.find_one({"_id": token})
    if not session:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user = await db.users.find_one({"email": session.get("email")})
    if not user or not user.get("email").endswith("@iiitkota.ac.in"):
        raise HTTPException(status_code=401, detail="Unauthorized")

    flow = create_flow()
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        login_hint=user.get("email"),
        enable_incremental_authorization=True,
        prompt="consent",
    )

    await db.sessions.update_one({"_id": token}, {"$set": {"oauth_state": state}})
    return RedirectResponse(authorization_url)

async def handle_callback(db, state, code):
    session = await db.sessions.find_one({"oauth_state": state})
    if not session:
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    flow = create_flow()
    flow.fetch_token(code=code)

    creds = flow.credentials
    user_info = await get_user_info(creds)

    if user_info:
        await db.users.update_one(
            {"email": user_info["email"]},
            {
                "$set": {
                    "name": user_info["name"],
                    "ai_auth": True,
                    "creds": {
                        "token": creds.token,
                        "refresh_token": creds.refresh_token,
                        "token_uri": creds.token_uri,
                        "client_id": creds.client_id,
                        "client_secret": creds.client_secret,
                        "scopes": creds.scopes,
                    },
                }
            },
        )

        return RedirectResponse("https://iiitk.devh.in/aidone")
    else:
        raise HTTPException(status_code=400, detail="Failed to get user info")

async def get_user_info(creds):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {creds.token}"}
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Error fetching user info: {str(e)}")
        return None