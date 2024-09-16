from fastapi import APIRouter, Depends, Request
from database import connect_to_database
from functions.apiwrapper import api_key_auth
from storage.driveauth import authenticate
from storage.driveauth import create_folder_and_get_id

router = APIRouter()


async def list_files(drive_service, FOLDER_ID):
    results = (
        drive_service.files()
        .list(q=f"'{FOLDER_ID}' in parents", fields="files(id, name, size)")
        .execute()
    )
    files = results.get("files", [])
    return files


@router.get("/files", dependencies=[Depends(api_key_auth)])
async def get_files(request: Request):
    api_key = request.headers.get("X-API-KEY")
    db = await connect_to_database()
    user = await db.sessions.find_one({"_id": api_key})
    if user:
        base_user = await db.users.find_one({"email": user.get("email")})
        drive_id = base_user.get("drive_id", None)
        if drive_id is None:
            drive_id = create_folder_and_get_id(
                base_user.get("_id"), "1p90vuxE8jp7mBwW63qj7rIwpiCuaYMEP"
            )
            await db.users.update_one(
                {"_id": base_user.get("_id")}, {"$set": {"drive_id": drive_id}}
            )
        drive_service = authenticate()
        files = await list_files(drive_service, drive_id)
        if not files:
            return {"message": "No files found in the folder."}
        else:
            return {"files": files}
