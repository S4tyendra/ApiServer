from .wca import wca
from fastapi import APIRouter
from .util_agents import w_agent
api = APIRouter()
api.include_router(wca, tags=["World cities api"], prefix="/wca")
api.include_router(w_agent, tags=["Web agent api"], prefix="/webagent")