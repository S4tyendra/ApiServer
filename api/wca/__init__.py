from fastapi import APIRouter

from .citiesinstate import router as city_router
from .countries import router as countrystates_router
from .statedata import router as states_router

wca = APIRouter()

wca.include_router(countrystates_router)
wca.include_router(states_router)
wca.include_router(city_router)
