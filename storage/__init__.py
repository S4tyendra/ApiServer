from fastapi import APIRouter

from storage import download, list_files, upload

app = APIRouter()

router = APIRouter()

router.include_router(download.router)
router.include_router(upload.router)
router.include_router(list_files.router)
