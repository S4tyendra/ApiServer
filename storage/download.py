import io
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from googleapiclient.http import MediaIoBaseDownload
from database import connect_to_database
from storage.driveauth import authenticate

router = APIRouter()

def download_file_generator(request: MediaIoBaseDownload, chunk_size: int = 1024 * 1024):
    """Generator that yields chunks of data, tracking progress."""
    buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(buffer, request, chunksize=chunk_size)
    done = False
    while not done:
        status, done = downloader.next_chunk()
        buffer.seek(0)
        yield buffer.read()
        buffer.seek(0)
        buffer.truncate(0)  # Clear the buffer after yielding its content

@router.get("/download/{file_id}")
async def download(request: Request, file_id: str):
    db = await connect_to_database()
    file = await db.files.find_one({"id": file_id})
    if not file:
        raise HTTPException(status_code=400, detail="File not found.")
    original_file_id = file.get("file_id")
    vs = await get_file_info(authenticate(), original_file_id)
    filename = vs.get("name")
    file_size = vs.get("size")
    if not original_file_id:
        raise HTTPException(status_code=404, detail="File not found.")

    drive_service = authenticate()
    headers = {
        'Content-Disposition': f'attachment; filename="{filename}"',
        'Content-Length': str(file_size)  # Add Content-Length header
    }

    media_request = drive_service.files().get_media(fileId=original_file_id)
    return StreamingResponse(download_file_generator(media_request), headers=headers, media_type='application/octet-stream')

async def get_file_info(drive_service, file_id):
    """Helper function to get file information from Drive."""
    file = drive_service.files().get(fileId=file_id, fields="id, name, size").execute()
    return file
