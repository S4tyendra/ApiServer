import ast
import secrets
from fastapi import Depends, APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Union
from functions.apiwrapper import  get_user
from functions.db import get_database

router = APIRouter()

class EditTopicNotes(BaseModel):
    code: str
    path: list
    content: str

@router.post("/edit-topic-notes", )
async def post_edit_topic_notes(data: EditTopicNotes, request: Request):
    user = await get_user(request, accept=["iiitk-android", "iiitk-win-lin"])
    pending_db = await get_database("iiitk_pending_topics")
    await pending_db.notes.insert_one({
        "_id": secrets.token_hex(8),
        "code": data.code,
        "path": data.path,
        "content": data.content,
        "email": user.get("email")
    })
    return {'message': 'Sent for review.'}

@router.get("/edit-topic-notes", )
async def get_edit_topic_notes(request: Request):
    await get_user(request, accept=["iiitk-android", "iiitk-win-lin"])
    pending_db = await get_database("iiitk_pending_topics")
    cursor = pending_db.notes.find({})
    data = await cursor.to_list(length=None)
    return JSONResponse(data)

class AdminEditTopicNotes(BaseModel):
    code: str
    path: List[Union[str, int]]
    content: str
    id: str

@router.post("/admin-edit-topic-data", )
async def only_admins_can_edit_topic_data(request: Request, data: AdminEditTopicNotes):
    user = await get_user(request, accept=["iiitk-android", "iiitk-win-lin"])
    if not user.get('is_admin', False):
        return JSONResponse({"error": "No Access"}, status_code=401)

    notes_db = await get_database('notes')
    collection = notes_db.IIITKOTA
    path = ["data"] + data.path if "data" not in data.path else data.path

    existing_doc = await collection.find_one({"_id": data.code})
    if existing_doc is None:
        existing_doc = {"_id": data.code, "data": {}}

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

    if isinstance(path[-1], int):
        while len(current_level) <= path[-1]:
            current_level.append({})
        current_level[path[-1]] = data.content
    else:
        current_level[path[-1]] = data.content

    result = await collection.update_one(
        {"_id": data.code},
        {"$set": existing_doc},
        upsert=True
    )

    pending_db = await get_database('iiitk_pending_topics')
    await pending_db.notes.delete_one({"_id": data.id})

    if result.modified_count > 0 or result.upserted_id is not None:
        return JSONResponse({"message": "Document updated successfully"}, status_code=200)
    else:
        return JSONResponse({"error": "No changes made to the document"}, status_code=400)

@router.delete("/admin-edit-topic-data", )
async def only_admins_can_delete_topic_data(request: Request, id: str):
    user = await get_user(request, accept=["iiitk-android", "iiitk-win-lin"])
    if not user.get('is_admin', False):
        return JSONResponse({"error": "No Access"}, status_code=401)

    pending_db = await get_database('iiitk_pending_topics')
    await pending_db.notes.delete_one({"_id": id})
    return "Ok"