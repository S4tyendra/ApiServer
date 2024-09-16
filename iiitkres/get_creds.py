from fastapi import APIRouter, HTTPException, Request

from database import connect_to_database

from fastapi import APIRouter, Request, HTTPException
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest
from database import connect_to_database
import google.generativeai as genai
from google.oauth2.credentials import Credentials

router = APIRouter()

SYSTEM_PROMPT = """
System:
You are an advanced multimodal AI assistant designed to help students create comprehensive and detailed class notes. Your primary function is to process various inputs from a class session, including text notes, images of handwritten notes or whiteboard content, and audio recordings of the entire class. Your goal is to synthesize this information into a well-structured, thorough set of notes that captures everything the teacher said and more.

## Input Processing Capabilities:
1. Text: Analyze and understand typed or OCR-processed handwritten notes.
2. Images: Interpret visual content from photographs of whiteboards, slides, or handwritten notes.
3. Audio: Transcribe and comprehend full audio recordings of class sessions, including the teacher's voice and any student interactions or discussions.

## Output Requirements:
1. Use Markdown formatting to create clear, well-organized notes.
2. Structure the notes logically, using appropriate headings, subheadings, and bullet points.
3. Include all key points, concepts, and examples mentioned by the teacher.
4. Expand on any topics that the teacher may have glossed over or missed, providing additional context or examples where necessary.
5. Incorporate relevant information from student questions or discussions.
6. Use code blocks for any programming examples or mathematical equations.
7. Create or describe diagrams where appropriate to illustrate complex concepts.

## Additional Responsibilities:
1. Clarify any ambiguous points from the lecture.
2. Provide additional examples or explanations for difficult concepts.
3. Include relevant cross-references to previous lessons or upcoming topics when applicable.
4. Highlight key terms, definitions, and important takeaways.
5. If the teacher assigns any homework or mentions upcoming assignments, include this information in a dedicated section.
6. If there are any gaps in the information provided, use your knowledge base to fill in missing details, clearly marking any such additions as supplementary information.
7. You shouldn't include timestamps like: 15:34 - 18:08.
8. Your response is notes, that's it. Dont write like The professor works through.. , The discussion continues, etc.
## Ethical Considerations:
1. Respect privacy by not identifying specific students in the notes.
2. Focus on educational content and filter out any irrelevant or inappropriate material that may have been captured in the recordings.

Your output should be a comprehensive, clear, and educational set of notes that not only captures the essence of the class but also enhances the student's understanding of the subject matter. Strive to create notes that would be valuable both for review and for students who may have missed the class.
 """


@router.get("/get_creds")
async def upload_content(request: Request):
    token = request.headers.get("X-API-KEY")
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    db = await connect_to_database()
    session = await db.sessions.find_one({"_id": token})
    if not session:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user = await db.users.find_one({"email": session.get("email")})
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if not user.get("ai_auth"):
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

    if creds.expired:
        try:
            creds.refresh(GoogleRequest())
            await db.users.update_one(
                {"email": user["email"]},
                {
                    "$set": {
                        "creds": {
                            "token": creds.token,
                            "refresh_token": creds.refresh_token,
                            "token_uri": creds.token_uri,
                            "client_id": creds.client_id,
                            "client_secret": creds.client_secret,
                            "scopes": creds.scopes,
                        }
                    }
                },
            )
        except Exception as e:
            raise HTTPException(status_code=401, detail="Failed to refresh token")
    try:
        return {
            "success": True,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating content: {str(e)}"
        )

    # file = genai.upload_file(path, mime_type=mime_type)
    # print(f"Uploaded file '{file.display_name}' as: {file.uri}")
    # return file


@router.post("/generate_content")
async def generate_content(request: Request):
    token = request.headers.get("X-API-KEY")
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    db = await connect_to_database()
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

    if creds.expired:
        try:
            creds.refresh(GoogleRequest())
            await db.users.update_one(
                {"email": user["email"]},
                {
                    "$set": {
                        "creds": {
                            "token": creds.token,
                            "refresh_token": creds.refresh_token,
                            "token_uri": creds.token_uri,
                            "client_id": creds.client_id,
                            "client_secret": creds.client_secret,
                            "scopes": creds.scopes,
                        }
                    }
                },
            )
        except Exception as e:
            raise HTTPException(status_code=401, detail="Failed to refresh token")

    try:
        genai.configure(credentials=creds)
        model = genai.GenerativeModel("gemini-1.5-pro")
        response = model.generate_content(
            "Tell me a short story about a robot learning to paint."
        )
        return {"content": response.text}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating content: {str(e)}"
        )
