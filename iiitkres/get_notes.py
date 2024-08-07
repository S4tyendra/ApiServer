import traceback

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from fastapi.responses import JSONResponse, StreamingResponse

from database import connect_to_database, connect_to_notes_database

router = APIRouter()


@router.get("/notes")
async def sen_notes_with_course_code(code: str, request: Request, response: Response):
    token = request.headers.get("X-API-KEY")
    if token:
        users_db = await connect_to_database()
        user = users_db.sessions.find_one({"_id": token})
        if user:
            notes_db = await connect_to_notes_database()
            notes = await notes_db.iiitkota.find_one({"_id": code.upper()})
            if notes:
                response = JSONResponse(notes)
                response.headers['Cache-Control'] = 'public, max-age=3600'
                # response.headers['Vary'] = 'Origin'
                response.headers['Access-Control-Allow-Origin'] = '*'
                return response
            else:
                return JSONResponse({"error": "Notes not found"}, status_code=404)
        else:
            return JSONResponse({"error": "User not found"}, status_code=404)
    else:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    # return HTTPException("Error Occured!")
