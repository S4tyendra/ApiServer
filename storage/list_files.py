
from fastapi import APIRouter
from storage.driveauth import authenticate
router = APIRouter()



async def list_files(drive_service, FOLDER_ID):
   results = drive_service.files().list(
       q=f"'{FOLDER_ID}' in parents",
       fields="files(id, name)"
   ).execute()
   files = results.get('files', [])
   return files

     
     
     
@router.get("/files")
async def get_files():
    drive_service = authenticate()
    files = await list_files(drive_service)
    if not files:
        return {'message': 'No files found in the folder.'}
    else:
        return {'files': files}