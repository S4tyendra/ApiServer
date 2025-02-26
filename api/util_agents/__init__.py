from fastapi import APIRouter
from .website_to_markdown import web2mdr

w_agent = APIRouter()

w_agent.include_router(web2mdr)