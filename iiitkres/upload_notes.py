


import traceback
from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from database import connect_to_database, connect_to_notes_database

router = APIRouter()

class NotesModel(BaseModel):
    title: str
    date: str
    data: str

@router.post("/upload-notes")
async def upload_notes(notes_data: NotesModel, request: Request, response: Response):
    token = request.headers.get("X-API-KEY")
    if not token:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    users_db = await connect_to_database()
    user = await users_db.sessions.find_one({"_id": token})
    if not user:
        return JSONResponse({"error": "User not found"}, status_code=404)
    
    notes_db = await connect_to_notes_database()
    points = genetares_points(notes_data.data)
    
    document_id = f"{notes_data.date.split(' ')[0]}|{user.get('email')}"
    course_name = notes_data.title.split("-")[1].strip()
    
    # Define the filter to find the document
    filter_query = {"_id": document_id}
    
    # Define the update operation
    update_query = {
        "$set": {
            course_name: notes_data.data,
            f"{course_name}_intro": points
        }
    }
    
    # Perform the upsert operation
    result = await notes_db.pending_notes.update_one(
        filter_query,
        update_query,
        upsert=True
    )
    
    if result.matched_count > 0:
        return JSONResponse({"message": "Notes updated successfully"}, status_code=200)
    else:
        return JSONResponse({"message": "New notes inserted successfully"}, status_code=200)
        
def genetares_points(data: str):
    KEY = "***"
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


@router.get("/pending-notes")
async def get_pending_notes(request: Request, response: Response):
    token = request.headers.get("X-API-KEY")
    if not token:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    users_db = await connect_to_database()
    user = await users_db.sessions.find_one({"_id": token})
    if not user:
        return JSONResponse({"error": "User not found"}, status_code=404)
    notes_db = await connect_to_notes_database()
    pending_notes = notes_db.pending_notes.find({})
    notes_list = []
    async for note in pending_notes:
        notes_list.append(note)
    return JSONResponse(notes_list)

@router.post("/pending-notes")
async def upload_pending_notes(data: NotesModel,  request: Request, response: Response, accept:bool = False,):
    token = request.headers.get("X-API-KEY")
    if not token:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    users_db = await connect_to_database()
    user = await users_db.sessions.find_one({"_id": token})
    if not user:
        return JSONResponse({"error": "User not found"}, status_code=404)
    email = user.get("email")
    if str(email).lower() not in ['2022kucp1033@iiitkota.ac.in']:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    notes_db = await connect_to_notes_database()

    document_id = f"{data.date.split(' ')[0]}"
    course_name = data.title.split("-")[1].strip()

    # Define the filter to find the document
    filter_query = {"_id": document_id}

    # Define the update operation

    update_query = {
        "$set": {
            course_name: data.data,
            f"{course_name}_intro": data.points
        }
    }

    if accept:
        result = await notes_db.iiitkota.update_one(
            filter_query,
            update_query,
            upsert=True
        )
        if result.matched_count > 0:
            return JSONResponse({"message": "Notes updated successfully"}, status_code=200)
        else:
            return JSONResponse({"message": "New notes inserted successfully"}, status_code=200)

    if not accept:
        result = await notes_db.pending_notes.delete_one(filter_query)
        if result.deleted_count > 0:
            return JSONResponse({"message": "Notes deleted successfully"}, status_code=200)
        else:
            return JSONResponse({"message": "Notes not found"}, status_code=404)


    

