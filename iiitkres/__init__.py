from fastapi import APIRouter

from .chatbot import router as chatbot_
from .delete_file import router as delete_router
from .list_pending_pulls import router as listpending
from .sendpdf import router as pdf_router

router = APIRouter()

router.include_router(pdf_router, )
router.include_router(chatbot_, )
router.include_router(delete_router)
router.include_router(listpending)
