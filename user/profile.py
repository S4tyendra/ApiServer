from fastapi import APIRouter, HTTPException, Request, Response
from database import connect_to_database
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/profile")
async def profile(request: Request, response: Response, _id: str):
    """
    Retrieve user profile based on the provided ID.
    Parameters:
    - request: Request object containing user request data.
    - response: Response object for returning the response.
    - _id: User ID to retrieve the profile for.
    Returns:
    - User profile data if accessible based on privacy settings.
    Raises:
    - HTTPException with status code 400 if the user is invalid or private.
    """
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
    """
    Retrieves user information based on cookie or API key.

    This function handles authentication based on either a cookie or an API key. It then
    retrieves user information from the database based on the authenticated email.

    Args:
        request (Request): The incoming request object.
        response (Response): The outgoing response object.

    Returns:
        JSONResponse: A JSON response containing user information or an error message.
    """

    # Check for authentication credentials
    cookie = request.cookies.get("_id-c")
    api_key = request.headers.get("X-API-KEY")
    auth_token = cookie or api_key

    # Connect to the database
    db = await connect_to_database()

    # Find the requester in the sessions collection
    requester_data = await db.sessions.find_one({"_id": auth_token})

    # Handle invalid user authentication
    if requester_data is None:
        raise HTTPException(status_code=400, detail="Invalid user")

    # Get the requester's email
    requester_email = requester_data.get("email")

    # Retrieve user data based on email and role
    if requester_email.endswith("@iiitkota.ac.in"):
        # Special handling for IIIT Kota users
        responser_data = await db.users.find_one({"email": requester_email})
        if responser_data is not None:
            # Include ai_auth status if present
            if responser_data.get("ai_auth", None) is not None:
                responser_data = await db.users.find_one(
                    {"email": requester_email},
                    projection=["_id", "email", "name", "picture", "tokens", "ai_auth"],
                )
            else:
                # Otherwise, default to False
                responser_data = await db.users.find_one(
                    {"email": requester_email},
                    projection=["_id", "email", "name", "picture", "tokens", "ai_auth"],
                )
                responser_data["ai_auth"] = False
    else:
        # General user retrieval
        responser_data = await db.users.find_one(
            {"email": requester_email},
            projection=["_id", "email", "name", "picture", "tokens"],
        )

    # Return the user data as a JSON response
    return JSONResponse(responser_data)
