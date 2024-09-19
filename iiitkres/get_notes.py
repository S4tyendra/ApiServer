import concurrent.futures
from youtubesearchpython import VideosSearch
from typing import List
from fastapi import HTTPException
import json

from bson import json_util
from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from database import connect_to_database, connect_to_notes_database

router = APIRouter()


@router.get("/notes")
async def get_notes_with_course_code(code: str, request: Request, response: Response):
    """
    Returns: Topic Wise notes for each course.
    """
    token = request.headers.get("X-API-KEY")
    if token:
        users_db = await connect_to_database()
        user = await users_db.sessions.find_one({"_id": token})
        if user:
            notes_db = await connect_to_notes_database()
            notes = await notes_db.IIITKOTA.find_one({"_id": code.upper()})
            if notes:
                response = JSONResponse(notes)
                response.headers["Cache-Control"] = "public, max-age=3600"
                response.headers["Access-Control-Allow-Origin"] = "*"
                return response
            else:
                return JSONResponse({"error": "Notes not found"}, status_code=404)
        else:
            return JSONResponse({"error": "User not found"}, status_code=404)
    else:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)


@router.get("/notes-dates")
async def get_notes_with_course_code(code: str, request: Request, response: Response):
    token = request.headers.get("X-API-KEY")
    if token:
        users_db = await connect_to_database()
        user = await users_db.sessions.find_one({"_id": token})
        if user:
            db = await connect_to_database(db_name="iiitk_notes")
            collection = getattr(db, code.upper())
            cursor = collection.find({})
            notes = await cursor.to_list(length=None)

            # Convert ObjectId to string for JSON serialization
            notes_json = json.loads(json_util.dumps(notes))

            response = JSONResponse(content=notes_json)
            response.headers["Cache-Control"] = "public, max-age=3600"
            response.headers["Access-Control-Allow-Origin"] = "*"
            return response
        else:
            return JSONResponse({"error": "User not found"}, status_code=404)
    else:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)


class UploadNotesModel(BaseModel):
    course_code: str
    date: str
    data: str
    points: list
    email: str


@router.post("/upload-md-notes")
async def upload_notes_on_that_date(
    data: UploadNotesModel, request: Request, response: Response
):
    token = request.headers.get("X-API-KEY")
    if token:
        users_db = await connect_to_database()
        session = await users_db.sessions.find_one({"_id": token})
        if not session:
            return JSONResponse({"error": "Unauthorized"}, status_code=401)
        user = await users_db.users.find_one({"email": session.get("email")})
        if user:
            if user.get("is_admin", False):
                db = await connect_to_database(db_name="notes")
                existing_note = await db.iiitkota.find_one({"_id": data.date})
                if existing_note:
                    await db.iiitkota.update_one(
                        {"_id": data.date},
                        {
                            "$set": {
                                data.course_code.upper(): data.data,
                                f"{data.course_code.upper()}_intro": data.points,
                            }
                        },
                    )
                else:
                    new_note = {
                        "_id": data.date,
                        data.course_code.upper(): data.data,
                        f"{data.course_code.upper()}_intro": data.points,
                    }
                    await db.iiitkota.insert_one(new_note)
                    await db.pending_notes.delete_one("_id")
                return JSONResponse({"message": "Notes uploaded successfully"})
            else:
                return JSONResponse(
                    {"error": "Only admin users can upload notes directly"},
                    status_code=403,
                )
        else:
            return JSONResponse({"error": "User not found"}, status_code=404)
    else:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)


#
# @router.get("/pending-notes")
# async def get_pending_notes(request: Request, response: Response):
#     token = request.headers.get("X-API-KEY")
#     if token:
#         users_db = await connect_to_database()
#         user = await users_db.sessions.find_one({"_id": token})
#         if user:
#             db = await connect_to_database(db_name="notes")
#             pending_notes = db.pending_notes.find({})
#             notes_list = []
#             async for note in pending_notes:
#                 notes_list.append(note)
#             return JSONResponse(notes_list)
#         else:
#             return JSONResponse({"error": "User not found"}, status_code=404)
#     else:
#         return JSONResponse({"error": "Unauthorized"}, status_code=401)
# #
#
# @router.post("/pending-notes")
# async def upload_pending_notes(
#     data: UploadNotesModel, request: Request, response: Response
# ):
#     token = request.headers.get("X-API-KEY")
#     if token:
#         users_db = await connect_to_database()
#         user = await users_db.sessions.find_one({"_id": token})
#         if user:
#             db = await connect_to_database(db_name="notes")
#             import secrets
#
#             pending_note = {
#                 "_id": secrets.token_hex(8),
#                 "course_code": data.course_code,
#                 "date": data.date,
#                 "data": data.data,
#                 "points": data.points,
#             }
#             await db.pending_notes.insert_one(pending_note)
#             return JSONResponse({"message": "Notes uploaded to pending queue"})
#         else:
#             return JSONResponse({"error": "User not found"}, status_code=404)
#     else:
#         return JSONResponse({"error": "Unauthorized"}, status_code=401)


class SearchRequest(BaseModel):
    search_terms: List[str]


class SearchResponse(BaseModel):
    youtube_links: List[str]


def search_youtube(query: str) -> str:
    try:
        search = VideosSearch(query, limit=1)
        result = search.result()
        if result["result"]:
            return result["result"][0]["link"]
        else:
            return None
    except Exception as e:
        print(f"Error searching for '{query}': {str(e)}")
        return None


def parallel_youtube_search(search_terms: List[str]) -> List[str]:
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = list(executor.map(search_youtube, search_terms))
    return results


@router.post("/search-youtube", response_model=SearchResponse)
async def search_youtube_route(ytrequest: SearchRequest, request: Request):
    token = request.headers.get("X-API-KEY")
    if not token:
        return JSONResponse({"error": "Unauthorised"})

    users_db = await connect_to_database()
    user = await users_db.sessions.find_one({"_id": token})
    if not user:
        return JSONResponse({"error": "Unauthorised"})
    youtube_links = parallel_youtube_search(ytrequest.search_terms)
    return SearchResponse(youtube_links=youtube_links)


# To use this router in your main FastAPI app:
# from fastapi import FastAPI
# app = FastAPI()
# app.include_router(router)
