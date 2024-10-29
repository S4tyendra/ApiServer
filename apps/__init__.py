from fastapi import APIRouter, Request, Response, Depends


router = APIRouter()

from .listapps import router as listapps_router

router.include_router(listapps_router)