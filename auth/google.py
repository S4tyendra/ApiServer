import os
import secrets
from fastapi import APIRouter, Request, Depends, HTTPException, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from google.auth.transport import requests
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token as google_id_token
import base64
from datetime import datetime

from database import connect_to_database 

router = APIRouter()
CLIENT_SECRETS_FILE = "auth/clientsecret.json"
SCOPES = ['https://www.googleapis.com/auth/userinfo.email', 
          'https://www.googleapis.com/auth/userinfo.profile',
          'openid']

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


red_map = {}

@router.get('/glogin')
async def login(redirect = None):
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES,
        # redirect_uri="http://localhost:8000/auth/googlesignin" 
        redirect_uri="https://aws-api.devh.in/auth/googlesignin" 
    )  # Use your FastAPI server's callback URL
    authorization_url, state = flow.authorization_url(
        access_type='offline', include_granted_scopes='true'
    )
    red_map[state] = redirect
    return RedirectResponse(authorization_url)



@router.get('/googlesignin')
async def callback(request: Request, response: Response):
    state = request.query_params.get('state')  # Extract state parameter
    if state in red_map:
        # redirect_uri="http://localhost:8000/auth/googlesignin" 
        redirect_uri = "https://aws-api.devh.in/auth/googlesignin"  # Update with your FastAPI server's callback URL
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE, scopes=SCOPES, state=state, redirect_uri=redirect_uri
        )

        flow.fetch_token(authorization_response=str(request.url).replace("http", "https"))

        id_token_data = google_id_token.verify_oauth2_token(flow.credentials.id_token, requests.Request())

        # Extract user data
        email = id_token_data['email']
        name = id_token_data['name']
        picture = id_token_data['picture']
        
        db = await connect_to_database()
        user = await db.users.find_one({"email": email})
        cookie = secrets.token_hex(32)
        
        if user is None:
            print(f"User not found, creating new user, {email}")
            # Create new user
            id = str(datetime.now().timestamp()).replace(".", "")
            await db.users.insert_one({"_id":id,"email": email, "name": name, "picture": picture, "role": "user"})
        user = await db.users.find_one({"email": email})
        print(user)
    
        id = user["_id"]
        await db.sessions.update_one({"email": email}, {"$set": {"created_at": datetime.now().timestamp()}})
        response.set_cookie(key="_id-c", value=cookie, httponly=False, secure=False)
        
        red_url = red_map.get(state)
        if red_url is not None:
            del red_map[state]
            return RedirectResponse(f"{red_url}?token={cookie}")
        return RedirectResponse("/")
        
    else:
        raise HTTPException(status_code=400, detail="Invalid state")
    
    
    
def xor_encrypt(data, key):
    encrypted_data = ""
    for i in range(len(data)):
        encrypted_data += chr(ord(data[i]) ^ ord(key[i % len(key)]))
    return base64.b64encode(encrypted_data.encode()).decode()

