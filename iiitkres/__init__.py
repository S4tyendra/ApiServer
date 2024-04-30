from fastapi import APIRouter

from .sendpdf import router as pdf_router
from .chatbot import router as chatbot_

router = APIRouter()

router.include_router(pdf_router, )
router.include_router(chatbot_, )
