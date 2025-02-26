import time
from typing import Optional, List, Dict, Any, Union
from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader
from starlette.requests import Request
from starlette.websockets import WebSocket
from functions.db import get_database

# Constants
API_KEY_NAME = "X-API-KEY"
DEFAULT_TOKENS = 10
MIN_WS_TOKENS = 5
TOKEN_OPERATION_SUCCEEDED = True
TOKEN_OPERATION_FAILED = False

# API Key Header Setup
api_key_header = APIKeyHeader(
    name=API_KEY_NAME,
    auto_error=False,
    scheme_name="API Key",
    description="API Key for authentication",
)

async def get_api_key(request: Request) -> Optional[str]:
    """Extract API key from various sources in the request."""
    return (request.headers.get(API_KEY_NAME) or 
            request.query_params.get("key") or 
            request.cookies.get("web-key") or 
            request.cookies.get("WEB-KEY"))

async def get_user(
    request: Request,
    accept: List[str],
    tokens_change: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Authenticate user via API key and manage token balance.
    
    Args:
        request: The incoming request
        accept: List of acceptable session types
        tokens_change: Amount to change tokens by (positive to add, negative to subtract)
    
    Returns:
        User document from database
    
    Raises:
        HTTPException: For authentication and token-related failures
    """
    api_key = await get_api_key(request)

    if not api_key:
        raise HTTPException(status_code=401, detail="Unauthorized, API key required")

    db = await get_database()
    accept_list = [str(i) for i in accept if i]
    
    # Construct appropriate query based on accept list
    query = {"_id": api_key}
    if accept_list:
        query["type"] = {"$in": accept_list}
    
    # Find session
    session = await db.sessions.find_one(query)
    if not session:
        raise HTTPException(status_code=401, detail="Unauthorized, invalid session")

    # Find user
    email = session.get('email')
    user = await db.users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized, user not found")

    # Handle token operations if needed
    current_tokens = user.get("tokens", DEFAULT_TOKENS)
    
    if tokens_change is not None:
        # Check if deduction would result in negative balance
        if tokens_change < 0 and current_tokens + tokens_change < 0:
            raise HTTPException(status_code=403, detail="Insufficient token balance")
            
        # Use atomic $inc operator to prevent race conditions
        await db.users.update_one(
            {"email": email},
            {
                "$set": {"last_accessed": time.time()},
                "$inc": {"tokens": tokens_change}
            }
        )
        
        # Update the user object with the new token count for return
        user["tokens"] = current_tokens + tokens_change
    else:
        await db.users.update_one(
            {"email": email},
            {"$set": {"last_accessed": time.time()}}
        )
    
    return user

async def get_ws_user(
    websocket: WebSocket,
    accept: List[str],
    token: str,
    token_cost: int = 0  # Default to no cost, but allow deduction if specified
) -> Optional[Dict[str, Any]]:
    """
    Authenticate WebSocket user, check token balance, and optionally deduct tokens.
    
    Args:
        websocket: The WebSocket connection
        accept: List of acceptable session types
        token: API key token
        token_cost: Number of tokens to deduct for this WebSocket operation
        
    Returns:
        User document from database or None if authentication fails
    """
    if not token:
        await websocket.accept()
        await websocket.send_text("Unauthorized, API key required. Please go to [Login page](/login) to set API key")
        await websocket.close(code=1008)
        return None

    db = await get_database()
    accept_list = [str(i) for i in accept if i]
    
    # Find session
    query = {"_id": token}
    if accept_list:
        query["type"] = {"$in": accept_list}
        
    session = await db.sessions.find_one(query)
    if not session:
        await websocket.accept()
        await websocket.send_text("Invalid session. Please go to [Login page](/login) to set API key")
        await websocket.close(code=1008)
        return None
    
    # Find user
    email = session.get('email')
    user = await db.users.find_one({"email": email})
    if not user:
        await websocket.accept()
        await websocket.send_text("Invalid user. Please go to [Login page](/login) to set API key")
        await websocket.close(code=1008)
        return None
    
    # Check minimum token requirement including any cost
    current_tokens = user.get("tokens", DEFAULT_TOKENS)
    required_tokens = MIN_WS_TOKENS + (token_cost if token_cost > 0 else 0)
    
    if current_tokens < required_tokens:
        await websocket.accept()
        await websocket.send_text(f"You need at least {required_tokens} tokens remaining. Please go to [Account page](https://account.devh.in/plans) to get more tokens!")
        await websocket.close(code=1008)
        return None
    
    # Update last accessed timestamp and deduct tokens if needed
    update_doc = {"$set": {"last_accessed": time.time()}}
    if token_cost > 0:
        update_doc["$inc"] = {"tokens": -token_cost}
        user["tokens"] = current_tokens - token_cost
    
    await db.users.update_one({"email": email}, update_doc)
    
    return user

async def update_user_tokens(email: str, tokens_change: int) -> bool:
    """
    Update a user's token balance.
    
    Args:
        email: User's email
        tokens_change: Amount to change tokens by (positive to add, negative to subtract)
        
    Returns:
        Boolean indicating success or failure
    """
    db = await get_database()
    
    try:
        # First check if user exists and has enough tokens for deduction
        if tokens_change < 0:
            user = await db.users.find_one({"email": email})
            if not user:
                return TOKEN_OPERATION_FAILED
                
            current_tokens = user.get("tokens", DEFAULT_TOKENS)
            if current_tokens + tokens_change < 0:
                return TOKEN_OPERATION_FAILED
        
        # Use atomic $inc operator to prevent race conditions
        result = await db.users.update_one(
            {"email": email},
            {
                "$set": {"last_accessed": time.time()},
                "$inc": {"tokens": tokens_change}
            }
        )
        
        return result.modified_count > 0
        
    except Exception as e:
        print(f"Error updating tokens for user {email}: {str(e)}")
        return TOKEN_OPERATION_FAILED

async def refund_tokens(email: str, tokens_to_refund: int) -> bool:
    """
    Refund tokens to a user's account.
    
    Args:
        email: User's email
        tokens_to_refund: Amount of tokens to refund (must be positive)
        
    Returns:
        Boolean indicating success or failure
    """
    if tokens_to_refund <= 0:
        print(f"Invalid refund amount: {tokens_to_refund}")
        return TOKEN_OPERATION_FAILED
        
    return await update_user_tokens(email, tokens_to_refund)
