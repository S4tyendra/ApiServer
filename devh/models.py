from datetime import datetime
from typing import List, Dict, Optional
from pydantic import BaseModel, Field, EmailStr

class Project(BaseModel):
    title: str
    desc: str
    id: str

class Education(BaseModel):
    title: str
    desc: str
    year: str

class Contact(BaseModel):
    VKey: str
    VVal: str
    href: str

class Admin(BaseModel):
    _id: Optional[str] = None
    name: str
    email: EmailStr
    password: str
    role: str = "admin"
    location: str = ""
    bio: str = ""
    expertise: List[str] = Field(default_factory=list)
    projects: List[Project] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    contact: List[Contact] = Field(default_factory=list)
    reactions: Dict[str, int] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class Blog(BaseModel):
    _id: Optional[str] = None
    title: str
    desc: str
    tags: List[str] = Field(default_factory=list)
    read: str
    author_id: Optional[str] = None
    reactions: Dict[str, int] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
