from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from .db_utils import get_admin_collection, get_blog_collection, hash_password, create_slug
from .auth import get_current_user, get_super_admin
from .models import Admin, Blog
from bson import json_util
import json

def convert_mongo_dates(data: dict) -> dict:
    if isinstance(data.get('created_at'), dict) and '$date' in data['created_at']:
        data['created_at'] = datetime.fromisoformat(data['created_at']['$date'].rstrip('Z'))
    if isinstance(data.get('updated_at'), dict) and '$date' in data['updated_at']:
        data['updated_at'] = datetime.fromisoformat(data['updated_at']['$date'].rstrip('Z'))
    return data

router = APIRouter()

@router.post("/admin", response_model=Admin)
async def create_admin(admin: Admin, current_user: dict = Depends(get_super_admin)):
    admin_collection = await get_admin_collection()
    
    if await admin_collection.find_one({"email": admin.email}):
        raise HTTPException(status_code=400, detail="Email already exists")
    
    admin_dict = admin.dict()
    admin_dict["_id"] = await create_slug(admin_dict["name"])
    admin_dict["password"] = hash_password(admin_dict["password"])
    admin_dict["created_at"] = datetime.utcnow()
    admin_dict["updated_at"] = datetime.utcnow()
    
    await admin_collection.insert_one(admin_dict)
    admin_dict["password"] = ""  # Clear password before returning
    return admin_dict

@router.put("/admin/{admin_id}", response_model=Admin)
async def update_admin(admin_id: str, admin_update: Admin, current_user: dict = Depends(get_current_user)):
    if current_user["_id"] != admin_id and current_user["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    admin_collection = await get_admin_collection()
    admin_dict = admin_update.dict(exclude_unset=True)
    
    if "password" in admin_dict:
        admin_dict["password"] = hash_password(admin_dict["password"])
    
    admin_dict["updated_at"] = datetime.utcnow()
    
    result = await admin_collection.update_one(
        {"_id": admin_id},
        {"$set": admin_dict}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Admin not found")
    
    updated_admin = await admin_collection.find_one({"_id": admin_id})
    updated_admin = convert_mongo_dates(updated_admin)
    updated_admin["password"] = ""  # Clear password before returning
    return updated_admin

@router.delete("/admin/{admin_id}")
async def delete_admin(admin_id: str, current_user: dict = Depends(get_super_admin)):
    admin_collection = await get_admin_collection()
    result = await admin_collection.delete_one({"_id": admin_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Admin not found")
    
    return {"message": "Admin deleted successfully"}

@router.post("/blog", response_model=Blog)
async def create_blog(blog: Blog, current_user: dict = Depends(get_current_user)):
    blog_collection = await get_blog_collection()
    
    blog_dict = blog.dict()
    blog_dict["_id"] = await create_slug(blog_dict["title"])
    blog_dict["author_id"] = current_user["_id"]
    blog_dict["created_at"] = datetime.utcnow()
    blog_dict["updated_at"] = datetime.utcnow()
    
    await blog_collection.insert_one(blog_dict)
    return blog_dict  # Return directly since we just created it with proper datetime objects

@router.put("/blog/{blog_id}", response_model=Blog)
async def update_blog(blog_id: str, blog_update: Blog, current_user: dict = Depends(get_current_user)):
    blog_collection = await get_blog_collection()
    blog = await blog_collection.find_one({"_id": blog_id})
    
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    
    if blog["author_id"] != current_user["_id"]:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    blog_dict = blog_update.dict(exclude_unset=True)
    blog_dict["updated_at"] = datetime.utcnow()
    
    await blog_collection.update_one(
        {"_id": blog_id},
        {"$set": blog_dict}
    )
    
    updated_blog = await blog_collection.find_one({"_id": blog_id})
    updated_blog = convert_mongo_dates(updated_blog)
    return updated_blog

@router.delete("/blog/{blog_id}")
async def delete_blog(blog_id: str, current_user: dict = Depends(get_current_user)):
    blog_collection = await get_blog_collection()
    blog = await blog_collection.find_one({"_id": blog_id})
    
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    
    if blog["author_id"] != current_user["_id"] and current_user["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    await blog_collection.delete_one({"_id": blog_id})
    return {"message": "Blog deleted successfully"}
