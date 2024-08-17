from fastapi import APIRouter

from .chatbot import router as chatbot_
from .sendpdf import router as pdf_router
from .get_notes import router as notes_router
from .auth import router as auth_router
router = APIRouter()

router.include_router(pdf_router, )
router.include_router(chatbot_, )
router.include_router(notes_router)
router.include_router(auth_router)