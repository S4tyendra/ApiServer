from datetime import datetime
from typing import List
import aiohttp
from fastapi import (
    APIRouter,
    Request,
    Response,
    UploadFile,
    File,
    HTTPException,
    Depends,
)
from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
    RedirectResponse,
    StreamingResponse,
)
import os
import tempfile
from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from motor.motor_asyncio import AsyncIOMotorClient
from google.oauth2.credentials import Credentials
import google.generativeai as genai

import os
import tempfile
from fastapi import Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient
from google.oauth2.credentials import Credentials
import google.generativeai as genai
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from github import Github
import os
import base64
import secrets
import mimetypes
from contextlib import asynccontextmanager
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from google.generativeai.types import file_types
from google.oauth2.credentials import Credentials
import tempfile
import traceback
from pydantic import BaseModel
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest
from functions.apiwrapper import get_user
from functions.db import get_database

router = APIRouter()


# GitHub setup
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "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")
REPO_NAME = "S4tyendra/images-host"
g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)



SYSTEM_PROMPT = """
You are Notes Creator - an advanced AI specifically designed to transform class content into comprehensive educational notes. Your sole purpose is converting lectures, images, and audio into well-structured study materials using Markdown formatting.

CORE CAPABILITIES:
- Process text, images, and audio from class sessions
- Create organized, detailed notes using Markdown only
- Use LaTeX for mathematical expressions ($inline$ or $$block$$)
- Include diagrams via mermaid code when needed
- Reference images using: !i!https://images.devh.in/search?q=image-search-query!i!. (So, image format is not ![](url) but !i!url!i!)

FORMATTING RULES:
- Use clean Markdown hierarchy (headings, lists, code blocks)
- No HTML elements
- No timestamps
- No narrative transitions or meta-commentary
- No disclaimers/notes/reminders at the end
- No professor/student identifiers

CONTENT GUIDELINES:
- Capture key concepts, examples, and discussions
- Add relevant context and clarifications
- Include homework/assignments in dedicated sections
- Mark supplementary additions clearly
- Focus solely on educational content
- Maintain academic tone and structure

STRICT BOUNDARIES:
- Generate class notes ONLY
- Decline all other requests politely. Just respond with a single white space nothing else!
- Do not engage in non-academic discussions
- Maintain focus on educational note-taking

Your responses should be pure educational notes - nothing more, nothing less. For any non-note-taking requests, simply respond: "I can only help with creating educational notes. Please provide class content to proceed."
"""



@router.post("/upload/")
async def upload_image(
    request: Request,
    file: UploadFile = File(...),
):
    if len(file.filename) > 52:
        raise HTTPException(status_code=400, detail="Filename too long")
    user = await get_user(request, accept=["iiitk-android", "iiitk-win-lin"])
    db = await get_database("image_storage")
    random_filename = secrets.token_hex(8) + os.path.splitext(file.filename)[1]
    content = await file.read()
    try:
        github_path = f"files/{random_filename}"
        repo.create_file(github_path, f"Upload {random_filename}", content)
        result = await db.user_files.insert_one(
            {
                "filename": random_filename,
                "github_path": github_path,
                "original_filename": file.filename,
                "email": user.get("email"),
            }
        )
        return {"id": str(result.inserted_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
from github import GithubException

@router.get("/file/{id}")
async def get_image(
    request: Request,
    id: str,
):
    db = await get_database("image_storage")
    image_data = await db.user_files.find_one({"_id": ObjectId(id)})
    if not image_data:
        raise HTTPException(status_code=404, detail="Image not found")
    try:
    
        # Try to get the file content directly first
        file_content = repo.get_contents(image_data["github_path"])
        decoded_content = base64.b64decode(file_content.content)
        if not decoded_content:
            # If the file is too large, use the Git Data API
            file = repo.get_contents(image_data["github_path"])
            blob = repo.get_git_blob(file.sha)
            decoded_content = base64.b64decode(blob.content)
        else:
            decoded_content = file_content.decoded_content 

        media_type, _ = mimetypes.guess_type(image_data["original_filename"])
        if not media_type:
            media_type = "application/octet-stream"

        return Response(content=decoded_content, media_type=media_type, headers={"Content-Disposition": f"attachment; filename={image_data['original_filename']}"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.post("/upload_to_gemini")
async def upload_to_gemini(
    request: Request,
    file: UploadFile = File(...),
):
    try:
        user_db = await get_database("fastapi_users_db")
        # Authentication checks
        api_key = request.headers.get("X-API-KEY")
        if not api_key:
            raise HTTPException(status_code=401, detail="API key is missing")

        session = await user_db["sessions"].find_one({"_id": api_key})
        if not session:
            raise HTTPException(status_code=401, detail="Invalid API key")

        user = await user_db["users"].find_one({"email": session.get("email")})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        if not user.get("email", "").endswith("@iiitkota.ac.in"):
            raise HTTPException(status_code=401, detail="Invalid email domain")

        if user.get("ai_auth") != True:
            raise HTTPException(status_code=401, detail="AI authentication not enabled")

        creds = user.get("creds")
        if not creds:
            raise HTTPException(status_code=401, detail="Credentials not found")

        # Create credentials object
        credentials = Credentials(
            token=creds.get("token"),
            refresh_token=creds.get("refresh_token"),
            token_uri=creds.get("token_uri"),
            client_id=creds.get("client_id"),
            client_secret=creds.get("client_secret"),
            scopes=creds.get("scopes"),
        )

        # Create temporary file
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=os.path.splitext(file.filename)[1]
        ) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        try:
            genai.configure(api_key="AIzaSyDOJ6TcI-ZFKICp6bR49x6bWXmOgA7F4vw")
            uploaded_file = genai.upload_file(path=temp_file_path)
            return JSONResponse(content=uploaded_file.to_dict(), status_code=201)
        finally:
            os.remove(temp_file_path)

    except HTTPException as he:
        return JSONResponse(content={"error": he.detail}, status_code=he.status_code)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


CLIENT_CONFIG = {
    "web": {
        "client_id": "400684228938-oaokv1bpm7ncrmj13i4vcm9bo3avheh9.apps.googleusercontent.com",
        "project_id": "iiitkres",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": "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",
        "redirect_uris": [
            "https://aws-api.devh.in/iiitk/auth",
            "http://localhost:8000/iiitk/auth",
        ],
        "javascript_origins": ["https://aws-api.devh.in", "http://localhost:8000"],
    }
}
SCOPES = [
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/generative-language.retriever",
    "openid",
]
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"


class Proto(BaseModel):
    name: str
    display_name: str
    mime_type: str
    size_bytes: int
    create_time: datetime
    update_time: datetime
    expiration_time: datetime
    sha256_hash: str
    uri: str
    state: str
class UserModelMessages(BaseModel):
    # Role must be 'user' or 'model'
    role: str
    parts: list[str]
class Message(BaseModel):
    messages: List[UserModelMessages]
    files: List[Proto]




async def refresh_token(db, user, creds):
    try:
        if creds.refresh_token:
            creds.refresh(GoogleRequest())
            new_creds_data = {
                "token": creds.token,
                "refresh_token": creds.refresh_token,  # Use the new refresh_token if available
                "token_uri": creds.token_uri,
                "client_id": creds.client_id,
                "client_secret": creds.client_secret,
                "scopes": creds.scopes,
            }
            await db.users.update_one(
                {"email": user["email"]}, {"$set": {"creds": new_creds_data}}
            )
            return creds
        else:
            return None
    except Exception as e:
        return None


@router.post("/generate_content")
async def generate_content(
    proto: Message,
    request: Request,
):
    user_db = await get_database("fastapi_users_db")
    token = request.headers.get("X-API-KEY")
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    db = user_db
    session = await db.sessions.find_one({"_id": token})
    if not session:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user = await db.users.find_one({"email": session.get("email")})
    if not user or not user.get("ai_auth"):
        raise HTTPException(status_code=401, detail="AI authentication required")

    creds_data = user.get("creds")
    if not creds_data:
        raise HTTPException(status_code=401, detail="Credentials not found")

    creds = Credentials(
        token=creds_data["token"],
        refresh_token=creds_data["refresh_token"],
        token_uri=creds_data["token_uri"],
        client_id=creds_data["client_id"],
        client_secret=creds_data["client_secret"],
        scopes=creds_data["scopes"],
    )
    creds = await refresh_token(db, user, creds)

    if proto.messages[0].parts[0] == "devider": # yes, it's devider. not divider
        # return text only response
        return Response(content="devider", media_type="text/plain")

    return StreamingResponse(
        content_generator(proto, creds), media_type="text/event-stream"
    )


def content_generator(proto: Message, creds: Credentials):
    try:
        messages = proto.messages.copy()
        # Convert messages to list of text and store in (messages_history)
        messages_history : list = []
        for message in messages:
            messages_history.append(message.dict())

        files = []
        for file in proto.files:
                
                file = file_types.File(
                    proto=dict(file.dict()),
                )
                files.append(file)

        genai.configure(credentials=creds)
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash" if files else "learnlm-1.5-pro-experimental",
            system_instruction=SYSTEM_PROMPT,
            safety_settings={
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            },
        )

        history=[
                {
                    "role": "user",
                    "parts": files,
                },
                *messages_history,
            ] if files else messages_history


        chat_session = model.start_chat(
            history=history,
        )
        response = chat_session.send_message(
            "Please analyze the provided class materials and create comprehensive educational notes following these guidelines:\n"
            "1. Extract and organize key academic concepts\n"
            "2. Include any mathematical formulas using LaTeX syntax\n"
            "3. Add relevant diagrams where needed using mermaid\n"
            "4. Structure content with clear headings and sections\n"
            "5. Focus only on academic/educational content\n"
            "6. Maintain proper Markdown formatting\n"
            "7. Exclude any non-academic discussions or tangential content",
            stream=True
        )
        for chunk in response:
            yield f"{chunk.text}"
    except Exception as e:
        
        traceback.print_exc()

