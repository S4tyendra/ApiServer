from fastapi import APIRouter

from .sendpdf import router as pdf_router
from .chatbot import router as chatbot_
from .delete_file import router as delete_router
from .list_pending_pulls import router as listpending


router = APIRouter()

router.include_router(pdf_router, )
router.include_router(chatbot_, )
router.include_router(delete_router)
router.include_router(listpending)
