


from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from database import connect_to_database



router = APIRouter()

class edit_topic_notes(BaseModel):
    code: str
    path: list
    content: str


@router.post("/edit-topic-notes")
async def edit_topic_notes(data:edit_topic_notes, request: Request):
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
    await db.notes.insert_one({
        "code": data.code,
        "path": data.path,
        "content": data.content
    })