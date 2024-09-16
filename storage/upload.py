from secrets import token_hex
import tempfile
from fastapi import APIRouter, Depends, Request, UploadFile, File, HTTPException
from googleapiclient.http import MediaFileUpload
from functions.apiwrapper import api_key_auth
from storage.driveauth import authenticate, create_folder_and_get_id
from database import connect_to_database

router = APIRouter()


async def upload_file(drive_service, file: UploadFile, FOLDER_ID):
    # Move the cursor to the end of the file to get the size
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)  # Move the cursor back to the start of the file

    if file_size > 10 * 1024 * 1024:  # 20 MB limit
        raise HTTPException(
            status_code=400, detail="File size exceeds the limit of 10 MB."
        )

    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(file.file.read())
        temp_file.flush()

        file_metadata = {"name": file.filename, "parents": [FOLDER_ID]}
        media = MediaFileUpload(
            temp_file.name, mimetype=file.content_type, resumable=True
        )
        request = drive_service.files().create(
            body=file_metadata, media_body=media, fields="id"
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"Uploaded {int(status.progress() * 100)}%")

    return [response.get("id"), file_size]


@router.post("/upload/", dependencies=[Depends(api_key_auth)])
async def upload(request: Request, file: UploadFile = File(...)):
    db = await connect_to_database()
    session_data = await db.sessions.find_one({"_id": request.headers.get("X-API-KEY")})

    if session_data:
        email = session_data.get("email")
        user = await db.users.find_one({"email": email})
        if user:
            drive_id = user.get("drive_id", None)
            if not drive_id:
                drive_id = create_folder_and_get_id(
                    user.get("_id"), "1p90vuxE8jp7mBwW63qj7rIwpiCuaYMEP"
                )
                await db.users.update_one(
                    {"_id": user.get("_id")}, {"$set": {"drive_id": drive_id}}
                )
            drive_service = authenticate()

            rand_file_id = f"{user.get('_id')}_{token_hex(16)}"
            uploaded_file_id, file_size = await upload_file(
                drive_service, file, drive_id
            )
            await db.files.insert_one(
                {
                    "id": rand_file_id,
                    "file_id": uploaded_file_id,
                    "file_name": file.filename,
                    "email": email,
                    "size": file_size,
                }
            )
            return {"uploaded_file_id": rand_file_id}
        else:
            raise HTTPException(status_code=400, detail="User not found.")
    else:
        raise HTTPException(status_code=400, detail="Session not found.")
