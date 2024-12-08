from functions.db import get_database
from datetime import datetime
from passlib.context import CryptContext
import re

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def get_admin_collection():
    db = await get_database()
    return db.devh_admins

async def get_blog_collection():
    db = await get_database()
    return db.devh_blog

async def create_slug(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

async def create_initial_admin():
    admin_collection = await get_admin_collection()
    if await admin_collection.count_documents({}) == 0:
        initial_admin = {
            "_id": "satya",
            "name": "Satya",
            "email": "satya@devh.in",
            "password": hash_password("Satya@8"),
            "role": "super_admin",
            "location": "",
            "bio": "",
            "expertise": [],
            "projects": [],
            "education": [],
            "contact": [],
            "reactions": {},
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        admin_collection.insert_one(initial_admin)
        return True
    return False
