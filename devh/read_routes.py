from fastapi import APIRouter, Depends, HTTPException
from .db_utils import get_admin_collection, get_blog_collection
from .auth import get_current_user
from bson import json_util
import json
from typing import List
from .models import Admin, Blog
from datetime import datetime
router = APIRouter()

@router.get("/admin/{admin_id}", response_model=Admin)
async def get_admin(admin_id: str, current_user: dict = Depends(get_current_user)):
    admin_collection = await get_admin_collection()
    admin = await admin_collection.find_one({"_id": admin_id})
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    admin['password'] = ''  # Set password to empty string
    if isinstance(admin['created_at'], dict) and '$date' in admin['created_at']:
        admin['created_at'] = datetime.fromisoformat(admin['created_at']['$date'].rstrip('Z'))
    if isinstance(admin['updated_at'], dict) and '$date' in admin['updated_at']:
        admin['updated_at'] = datetime.fromisoformat(admin['updated_at']['$date'].rstrip('Z'))
    return admin
@router.get("/admins", response_model=List[Admin])
async def get_admins():
    admin_collection = await get_admin_collection()
    admins = await admin_collection.find().to_list(None)
    for admin in admins:
        admin['password'] = ''  # Set password to empty string
        if isinstance(admin['created_at'], dict) and '$date' in admin['created_at']:
            admin['created_at'] = datetime.fromisoformat(admin['created_at']['$date'].rstrip('Z'))
        if isinstance(admin['updated_at'], dict) and '$date' in admin['updated_at']:
            admin['updated_at'] = datetime.fromisoformat(admin['updated_at']['$date'].rstrip('Z'))
    return admins

@router.get("/blog/{blog_id}", response_model=Blog)
async def get_blog(blog_id: str):
    blog_collection = await get_blog_collection()
    blog = await blog_collection.find_one({"_id": blog_id})
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    return Blog(**json.loads(json_util.dumps(blog)))

    
@router.get("/blogs", response_model=List[Blog])
async def get_blogs():
    blog_collection = await get_blog_collection()
    blogs = await blog_collection.find().to_list(None)
    return [Blog(**json.loads(json_util.dumps(blog))) for blog in blogs]
@router.get("/admin/{admin_id}/blogs", response_model=List[Blog])
async def get_admin_blogs(admin_id: str):
    blog_collection = await get_blog_collection()
    blogs = await blog_collection.find({"author_id": admin_id}).to_list(None)
    return [Blog(**json.loads(json_util.dumps(blog))) for blog in blogs]
