import ast
import secrets

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from bson.json_util import dumps
from fastapi.responses import JSONResponse
from pymongo import UpdateOne
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from database import connect_to_database
from pydantic import BaseModel
from typing import List, Union

from database import connect_to_database

router = APIRouter()


class edit_topic_notes(BaseModel):
    code: str
    path: list
    content: str


@router.post("/edit-topic-notes")
async def post_edit_topic_notes(data: edit_topic_notes, request: Request):
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
    pending_db = await connect_to_database("iiitk_pending_topics")
    await pending_db.notes.insert_one(
        {
            "_id": secrets.token_hex(8),
            "code": data.code,
            "path": data.path,
            "content": data.content,
            "email": session.get("email"),
        }
    )
    return {"message": "Waiting for review."}


@router.get("/edit-topic-notes")
async def get_edit_topic_notes(request: Request):
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

    pending_db = await connect_to_database("iiitk_pending_topics")

    # Convert cursor to list of documents
    cursor = pending_db.notes.find({})
    data = await cursor.to_list(length=None)
    data = dumps(data)
    data = ast.literal_eval(data)

    return JSONResponse(data)


class AdminEditTopicNotes(BaseModel):
    code: str
    path: List[Union[str, int]]
    content: str
    id: str


@router.post("/admin-edit-topic-data")
async def only_admins_can_edit_topic_data(request: Request, data: AdminEditTopicNotes):
    # ... (previous authentication code remains the same)

    notes_db = await connect_to_database("notes")
    collection = notes_db.IIITKOTA
    if "data" not in data.path:
        path = ["data"] + data.path
    else:
        path = data.path

    _id = data.code
    new_content = data.content

    # Attempt to find the existing document
    existing_doc = await collection.find_one({"_id": _id})

    if existing_doc is None:
        # If document doesn't exist, create a new one
        existing_doc = {"_id": _id, "data": {}}

    # Navigate through the path and create nested structure if it doesn't exist
    current_level = existing_doc
    for i, key in enumerate(path[:-1]):
        if isinstance(key, int):
            if not isinstance(current_level, list):
                current_level = []
            while len(current_level) <= key:
                current_level.append({} if i < len(path) - 2 else [])
            current_level = current_level[key]
        else:
            if key not in current_level:
                current_level[key] = {} if i < len(path) - 2 else []
            current_level = current_level[key]

    # Set the value at the final level
    if isinstance(path[-1], int):
        while len(current_level) <= path[-1]:
            current_level.append({})
        current_level[path[-1]] = new_content
    else:
        current_level[path[-1]] = new_content

    # Perform the upsert operation
    result = await collection.update_one(
        {"_id": _id}, {"$set": existing_doc}, upsert=True
    )

    # Delete from pending database
    pending_db = await connect_to_database("iiitk_pending_topics")
    await pending_db.notes.delete_one({"_id": data.id})

    if result.modified_count > 0 or result.upserted_id is not None:
        return JSONResponse(
            {"message": "Document updated successfully"}, status_code=200
        )
    else:
        return JSONResponse(
            {"error": "No changes made to the document"}, status_code=400
        )


@router.delete("/admin-edit-topic-data")
async def only_admins_can_delete_topic_data(request: Request, id: str):
    token = request.headers.get("X-API-KEY")
    if not token:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    users_db = await connect_to_database()
    session = await users_db.sessions.find_one({"_id": token})
    if not session:
        return JSONResponse({"error": "User not found"}, status_code=404)
    email = session.get("email")
    user = await users_db.users.find_one({"email": email})
    if not user:
        return JSONResponse({"error": "No Access"}, status_code=401)
    if not user.get("is_admin", False):
        return JSONResponse({"error": "No Access"}, status_code=401)

    pending_db = await connect_to_database("iiitk_pending_topics")
    await pending_db.notes.delete_one({"_id": id})
    return "Ok"
