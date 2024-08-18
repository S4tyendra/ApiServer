from fastapi import APIRouter, Request, Depends, HTTPException, Response
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest
import requests
from database import connect_to_database
import os
import json
local = bool(os.getenv("LOCAL", False))
router = APIRouter()

CLIENT_SECRETS_FILE = "iiitkres/clientsecret.json"
SCOPES = [
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/generative-language.retriever',
    'openid'
]

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

def create_flow():
    return Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri="http://localhost:8000/iiitk/auth" if local else "https://aws-api.devh.in/iiitk/auth"
    )

@router.get("/auth")
async def auth(request: Request, response: Response, state: str = None, code: str = None):
    if not state and not code:
        # Initial authorization request
        token = request.headers.get("X-API-KEY")
        if not token:
            raise HTTPException(status_code=401, detail="Unauthorized")
        
        db = await connect_to_database()
        session = await db.sessions.find_one({"_id": token})
        if not session:
            raise HTTPException(status_code=401, detail="Unauthorized")
        
        user = await db.users.find_one({"email": session.get('email')})
        if not user or not user.get('email').endswith("@iiitkota.ac.in"):
            raise HTTPException(status_code=401, detail="Unauthorized")
        
        flow = create_flow()
        authorization_url, state = flow.authorization_url(
            access_type="offline",
            login_hint=user.get('email'),
            enable_incremental_authorization=True,
        )
        
        # Store the state in the session for later verification
        await db.sessions.update_one({"_id": token}, {"$set": {"oauth_state": state}})
        print(authorization_url)
        return RedirectResponse(authorization_url)
    
    elif state and code:
        # Callback after user grants permission
        db = await connect_to_database()
        session = await db.sessions.find_one({"oauth_state": state})
        if not session:
            raise HTTPException(status_code=400, detail="Invalid state parameter")
        
        flow = create_flow()
        flow.fetch_token(code=code)
        
        creds = flow.credentials
        user_info = await get_user_info(creds)
        
        if user_info:
            # Update user in database
            await db.users.update_one(
                {"email": user_info['email']},
                {
                    "$set": {
                        "name": user_info['name'],
                        "ai_auth": True,
                        "creds": {
                            "token": creds.token,
                            "refresh_token": creds.refresh_token,
                            "token_uri": creds.token_uri,
                            "client_id": creds.client_id,
                            "client_secret": creds.client_secret,
                            "scopes": creds.scopes
                        }
                    }
                }
            )
            
            return RedirectResponse("https://iiitk.devh.in/aidone")
        else:
            raise HTTPException(status_code=400, detail="Failed to get user info")
    
    else:
        raise HTTPException(status_code=400, detail="Invalid request")

async def get_user_info(creds):
    try:
        userinfo_endpoint = "https://www.googleapis.com/oauth2/v3/userinfo"
        response = requests.get(userinfo_endpoint, headers={'Authorization': f'Bearer {creds.token}'})
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to fetch user info. Status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error fetching user info: {str(e)}")
        return None
    
import google.generativeai as genai
from google.oauth2.credentials import Credentials

@router.post("/generate_content")
async def generate_content(request: Request):
    token = request.headers.get("X-API-KEY")
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    db = await connect_to_database()
    session = await db.sessions.find_one({"_id": token})
    if not session:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    user = await db.users.find_one({"email": session.get('email')})
    if not user or not user.get('ai_auth'):
        raise HTTPException(status_code=401, detail="AI authentication required")
    
    creds_data = user.get('creds')
    if not creds_data:
        raise HTTPException(status_code=401, detail="Credentials not found")
    
    creds = Credentials(
        token=creds_data['token'],
        refresh_token=creds_data['refresh_token'],
        token_uri=creds_data['token_uri'],
        client_id=creds_data['client_id'],
        client_secret=creds_data['client_secret'],
        scopes=creds_data['scopes']
    )
    
    # Check if the token is expired and refresh if necessary
    if creds.expired:
        try:
            creds.refresh(GoogleRequest())
            # Update the refreshed credentials in the database
            await db.users.update_one(
                {"email": user['email']},
                {"$set": {"creds": {
                    "token": creds.token,
                    "refresh_token": creds.refresh_token,
                    "token_uri": creds.token_uri,
                    "client_id": creds.client_id,
                    "client_secret": creds.client_secret,
                    "scopes": creds.scopes
                }}}
            )
        except Exception as e:
            raise HTTPException(status_code=401, detail="Failed to refresh token")
    
    try:
        genai.configure(credentials=creds)
        model = genai.GenerativeModel('gemini-1.5-pro')
        response = model.generate_content("Tell me a short story about a robot learning to paint.")
        return {"content": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating content: {str(e)}")