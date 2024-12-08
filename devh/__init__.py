from fastapi import APIRouter
from .read_routes import router as read_router
from .write_routes import router as write_router

router = APIRouter(prefix="/devh")
router.include_router(read_router)
router.include_router(write_router)

# # Initialize the database with the first admin
# from .test import test_init_db
# test_init_db()