import os
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse
from google.auth.transport import requests
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow

router = APIRouter()
CLIENT_SECRETS_FILE = "auth/clientsecret.json"
SCOPES = ['https://www.googleapis.com/auth/userinfo.email', 
          'https://www.googleapis.com/auth/userinfo.profile',
          'openid']

@router.get('/glogin')
async def login():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, redirect_uri="https://aws-api.devh.in/auth/googlesignin" 
    )  # Use your FastAPI server's callback URL
    authorization_url, state = flow.authorization_url(
        access_type='offline', include_granted_scopes='true'
    )
    return RedirectResponse(authorization_url)

from google.oauth2 import id_token as google_id_token

@router.get('/googlesignin')
async def callback(request: Request):
    state = request.query_params.get('state')  # Extract state parameter
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

    return {"email": email, "name": name, "picture": picture}