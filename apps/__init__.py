from fastapi import APIRouter, Request, Response, Depends


router = APIRouter()

from .listapps import router as listapps_router
from .detail import router as detail_router
from .approve import router as approve_router
router.include_router(listapps_router)
router.include_router(detail_router)
router.include_router(approve_router)