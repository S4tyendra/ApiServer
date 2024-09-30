import json

from bson import json_util
from fastapi import APIRouter, Request, Response, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from functions.apiwrapper import api_key_auth, get_user
from functions.db import get_database

router = APIRouter()


@router.get("/notes", dependencies=[Depends(lambda: api_key_auth(accept=["iiitk-android","iiitk-win-lin",],),),],)
async def get_notes_with_course_code(code: str, request: Request, response: Response):
    """
    Returns: Topic Wise notes for each course.
    """
    user = await get_user(request, accept=["iiitk-android", "iiitk-win-lin", ])
    notes_db = await get_database(db_name="notes")
    notes = await notes_db.IIITKOTA.find_one({"_id": code.upper()})
    if notes:
        response = JSONResponse(notes)
        response.headers["Cache-Control"] = "public, max-age=3600"
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response
    else:
        return JSONResponse({"error": "Notes not found"}, status_code=404)


@router.get("/notes-dates",dependencies=[Depends(lambda: api_key_auth(accept=["iiitk-android","iiitk-win-lin",],),),])
async def get_notes_with_course_code(code: str, request: Request, response: Response):
    user = await get_user(request, accept=["iiitk-android", "iiitk-win-lin", ])
    db = await get_database(db_name="iiitk_notes")
    collection = getattr(db, code.upper())
    cursor = collection.find({})
    notes = await cursor.to_list(length=None)

    # Convert ObjectId to string for JSON serialization
    notes_json = json.loads(json_util.dumps(notes))

    response = JSONResponse(content=notes_json)
    response.headers["Cache-Control"] = "public, max-age=3600"
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response


class UploadNotesModel(BaseModel):
    course_code: str
    date: str
    data: str
    points: list
    email: str


@router.post("/upload-md-notes",dependencies=[Depends(lambda: api_key_auth(accept=["iiitk-android","iiitk-win-lin",],),),])
async def upload_notes_on_that_date(data: UploadNotesModel, request: Request, response: Response):
    user = await get_user(request, accept=["iiitk-android", "iiitk-win-lin", ])
    db = await get_database(db_name="notes")
    existing_note = await db.iiitkota.find_one({"_id": data.date})
    if existing_note:
        await db.iiitkota.update_one({"_id": data.date}, {"$set": {data.course_code.upper(): data.data,
                                                                   f"{data.course_code.upper()}_intro": data.points, }}, )
    else:
        new_note = {"_id": data.date, data.course_code.upper(): data.data,
                    f"{data.course_code.upper()}_intro": data.points, }
        await db.iiitkota.insert_one(new_note)
        await db.pending_notes.delete_one("_id")
    return JSONResponse({"message": "Notes uploaded successfully"})

from pydantic import BaseModel
from typing import List
from youtubesearchpython import VideosSearch
import concurrent.futures


class SearchRequest(BaseModel):
    search_terms: List[str]


class SearchResponse(BaseModel):
    youtube_links: List[str]


def search_youtube(query: str) -> str:
    try:
        search = VideosSearch(query, limit=1)
        result = search.result()
        if result['result']:
            return result['result'][0]['link']
        else:
            return None
    except Exception as e:
        print(f"Error searching for '{query}': {str(e)}")
        return None


def parallel_youtube_search(search_terms: List[str]) -> List[str]:
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = list(executor.map(search_youtube, search_terms))
    return results


@router.post("/search-youtube", response_model=SearchResponse, dependencies=[Depends(lambda: api_key_auth(accept=["iiitk-android","iiitk-win-lin",]))])
async def search_youtube_route(ytrequest: SearchRequest, request:Request):
    user = await get_user(request, accept=["iiitk-android", "iiitk-win-lin", ])
    youtube_links = parallel_youtube_search(ytrequest.search_terms)
    return SearchResponse(youtube_links=youtube_links)


