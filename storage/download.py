
import io
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from googleapiclient.http import  MediaIoBaseDownload

import io

from storage.driveauth import authenticate

router = APIRouter()

async def get_file_info(drive_service, file_id):
    file = drive_service.files().get(fileId=file_id).execute()
    return file

async def download_file(drive_service, file_id):
    request = drive_service.files().get_media(fileId=file_id)
    def iterfile():
        downloader = MediaIoBaseDownload(io.BytesIO(), request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            yield downloader._fd.getvalue() 
            downloader._fd.seek(0)  
            downloader._fd.truncate(0)

    file_info = await get_file_info(drive_service, file_id)
    file_name = file_info.get('name', 'downloaded_file')
    headers = {'Content-Disposition': f'attachment; filename="{file_name}"'}
    return StreamingResponse(iterfile(), media_type='application/octet-stream', headers=headers)



@router.get("/download/{file_id}")
async def download(file_id: str):
    drive_service = authenticate()
    return await download_file(drive_service, file_id)