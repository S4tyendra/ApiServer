from fastapi import APIRouter, HTTPException, Request, Response
from database import connect_to_database

router = APIRouter()


@router.get("/profile")
async def profile(request: Request, response: Response, _id: str):
    cookie = request.cookies.get("_id-c")
    db = await connect_to_database()
    requester_data = await db.sessions.find_one({"_id": cookie})
    requester_email = requester_data.get("email")
    responser_data = await db.users.find_one({"_id": _id})
    if responser_data is None:
        raise HTTPException(status_code=400, detail="Invalid user")
    if responser_data.get("email") == requester_email:
        return responser_data
    else:
        private = responser_data.get("is_private")
        if private:
            if responser_data.get("followers") is None:
                responser_data["followers"] = []
            if requester_email in responser_data.get("followers"):
                return responser_data
            else:
                raise HTTPException(status_code=400, detail="Private user")
        else:
            return responser_data


@router.get("/me")
async def me(request: Request, response: Response):
    cookie = request.cookies.get("_id-c")
    api_key = request.headers.get("X-API-KEY")
    cookie = api_key or cookie
    db = await connect_to_database()
    requester_data = await db.sessions.find_one({"_id": cookie})
    if requester_data is None:
        raise HTTPException(status_code=400, detail="Invalid user")
    requester_email = requester_data.get("email")
    responser_data = await db.users.find_one({"email": requester_email}, projection=["_id", "email", "name", "picture", "tokens"])
    return responser_data
