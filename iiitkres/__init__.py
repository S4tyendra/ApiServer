from fastapi import APIRouter

from .chatbot import router as chatbot_
from .upload_notes import router as upload_router
from .get_notes import router as notes_router
from .auth import router as auth_router
from .edit_notes import router as edit_notes_router
from .get_creds import router as get_creds_router
router = APIRouter()

router.include_router(upload_router, )
router.include_router(chatbot_, )
router.include_router(notes_router)
router.include_router(auth_router)
router.include_router(get_creds_router)
router.include_router(edit_notes_router)