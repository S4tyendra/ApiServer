
import io
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from googleapiclient.http import MediaFileUpload

import tempfile
import io
from fastapi import HTTPException
from googleapiclient.http import MediaFileUpload
router = APIRouter()

from functions.apiwrapper import api_key_auth
from storage.driveauth import authenticate


async def upload_file(drive_service, file: UploadFile, FOLDER_ID):
    mime_type = file.content_type
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > 20 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds the limit of 5 MB.")
    
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(file.file.read())
        temp_file.flush()
        file_metadata = {'name': file.filename, 'parents': [FOLDER_ID]}
        
        media = MediaFileUpload(temp_file.name, mimetype=mime_type)
        
        uploaded_file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
    
    return uploaded_file.get('id')

@router.post("/upload/", dependencies=[Depends(api_key_auth)])
async def upload(file: UploadFile = File(...)):
    drive_service = authenticate()
    uploaded_file_id = await upload_file(drive_service, file)
    return {"uploaded_file_id": uploaded_file_id}



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("upload:app",reload=True, host="127.0.0.1", port=8000)

