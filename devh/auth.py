from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from .db_utils import get_admin_collection, verify_password

security = HTTPBasic()

async def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    admin_collection = await get_admin_collection()
    admin = await admin_collection.find_one({"email": credentials.username})
    
    if not admin or not verify_password(credentials.password, admin["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return admin

async def get_super_admin(admin = Depends(get_current_user)):
    if admin["role"] != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin privileges required"
        )
    return admin
