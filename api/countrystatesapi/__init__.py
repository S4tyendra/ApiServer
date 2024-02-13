from fastapi import APIRouter

from .countries import router as countrystates_router
from .statedata import router as states_router
from .citiesinstate import router as city_router

router = APIRouter()

router.include_router(countrystates_router, prefix="/wca")
router.include_router(states_router, prefix="/wca")
router.include_router(city_router, prefix="/wca")
