import json
import secrets
import traceback

from bson import json_util
from fastapi import APIRouter, Request, Response, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from functions.apiwrapper import  get_user
from functions.db import get_database

router = APIRouter()


class NotesModel(BaseModel):
    title: str
    date: str
    data: str
    points: list = []


@router.post("/upload-notes" , )
async def upload_notes(notes_data: NotesModel, request: Request, response: Response):
    user = await get_user(request, accept=["iiitk-android", "iiitk-win-lin", ])
    notes_db = await get_database('iiitk_pending_notes')
    if len(notes_data.points) < 1:
        points = genetares_points(notes_data.data)
    else:
        points = notes_data.points
    course_code = notes_data.title.split("-")[1].strip()
    email = user.get('email')

    await getattr(notes_db, f'{course_code}').insert_one(dict(
        _id=secrets.token_hex(16),
        date=notes_data.date,
        email=email,
        points=points,
        data=notes_data.data
    ))
    return {"message":"Operation Successful"}


def genetares_points(data: str):
    KEY = "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"
    from groq import Groq
    client = Groq(
        api_key=KEY,
    )
    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": "Response ,must be in JSON\n\nYour job is to return the list of points discussed based on user input. each point must be in one or 2 words, Give as python programmable list without variable, and any unnecessary text such as Here are 10 single-worded points to get an idea about the content, etc. just list. thats it. not even with backquotes. Max 10 points\n\n"
            },
            {
                "role": "user",
                "content": data
            },
            {
                "role": "user",
                "content": "Give me points as python list"
            }
        ],
        temperature=0.2,
        max_tokens=520,
        top_p=1,
        stream=False,
        stop=None,
    )
    try:
        import ast
        print(completion.choices[0].message.content)
        json = ast.literal_eval(completion.choices[0].message.content)
        return json
    except:
        traceback.print_exc()
        return []


class NotesModel(BaseModel):
    code: str
    date: str
    data: str
    points: list
    email: str


@router.post("/upload-notes-admin", )
async def upload_notes(notes_data: NotesModel, request: Request, response: Response):
    user = await get_user(request, accept=["iiitk-android", "iiitk-win-lin", ])
    if not user.get('is_admin', False):
        return JSONResponse({"error": "No Access"}, status_code=401)
    notes_db = await get_database('iiitk_notes')
    course_code = notes_data.code
    email = user.get('email')
    await getattr(notes_db, f'{course_code}').insert_one(dict(
        date=notes_data.date,
        email=notes_data.email,
        points=notes_data.points,
        data=notes_data.data
    ))
    pending_db = await get_database('iiitk_pending_notes')
    await getattr(pending_db, f'{course_code}').delete_one(dict(
        date=notes_data.date,
        email=notes_data.email,
    ))

    return {"message":"Operation Successful"}


@router.delete("/upload-notes-admin", )
async def upload_notes(code,date,email_, request: Request, response: Response):
    user = await get_user(request, accept=["iiitk-android", "iiitk-win-lin", ])
    if not user:
        return JSONResponse({"error": "No Access"}, status_code=401)
    if not user.get('is_admin', False):
        return JSONResponse({"error": "No Access"}, status_code=401)
    course_code = code
    pending_db = await get_database('iiitk_pending_notes')
    await getattr(pending_db, f'{course_code}').delete_one(dict(
        date=date,
        email=email_,
    ))

    return {"message":"Operation Successful"}


@router.get("/pending-notes")
async def get_pending_notes(request: Request, response: Response):
    user = await get_user(request, accept=["iiitk-android", "iiitk-win-lin", ])
    notes_db = await get_database('iiitk_pending_notes')

    # Fetch all collections from the database
    collections = await notes_db.list_collection_names()

    result = {}
    for collection_name in collections:
        collection = notes_db[collection_name]
        cursor = collection.find({})
        documents = await cursor.to_list(length=None)
        result[collection_name] = json.loads(json_util.dumps(documents))

    return JSONResponse(content=result)

