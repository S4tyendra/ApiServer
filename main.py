from fastapi.middleware.cors import CORSMiddleware
import logging
import os
import time

import aiofiles
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Form, Request, Response
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
# from pyrogram import idle

# from tgbot.main import bot
from fastapi import FastAPI, Request
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import google.generativeai as genai
from api.countrystatesapi import router as countrystates_router
from auth.login import router as auth_router
from database import connect_to_database
from user.profile import router as user_router
from stripe_pay.payments import app as stripe_router
from iiitk.delete_file import router as iiitk_delete_router
from iiitk.list_pending_pulls import router as iiitk_router
from auth.google import router as google_router

os.system("git pull ")


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler('applog.txt'), logging.StreamHandler()])

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")


# @app.on_event("startup")
# async def startup_event():
#     await bot.start()
#     logging.info("Bot started!")


async def clear_log():
    # await bot.send_document(-1001543238877, "applog.txt")
    # async with aiofiles.open('applog.txt', 'w') as f:
        pass


def delete_temp():
    for file in os.listdir("temp"):
        if file.endswith(".pdf"):
            os.remove(f"temp/{file}")


# Set up scheduler
scheduler = AsyncIOScheduler()
scheduler.add_job(clear_log, 'interval', minutes=10)
scheduler.add_job(delete_temp, 'interval', minutes=5)
scheduler.start()
logging.info("Scheduler started!")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_request(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    response.headers["X-Process-Time"] = str(time.time() - start_time)
    logging.debug(
        f"{request.method} - {request.url} / {request.headers.get('cookie')} /{request.headers.get('x-api-key')}")
    return response


if os.path.exists(".env"):
    from dotenv import load_dotenv

    load_dotenv()

# Include routers
app.include_router(auth_router, tags=[
    "auth"], prefix="/auth", include_in_schema=False)
app.include_router(user_router, tags=["user"], prefix="/user")
app.include_router(countrystates_router, tags=[
    "World cities api", ], prefix="/api")
app.include_router(stripe_router, tags=["stripe"], prefix="/stripe", include_in_schema=False)
app.include_router(iiitk_delete_router, tags=["IIITK"], prefix="/iiitk",include_in_schema=False)
app.include_router(iiitk_router, tags=["IIITK"], prefix="/iiitk", include_in_schema=False)
app.include_router(google_router, tags=["GAUTH"], prefix="/auth")



@app.get("/", include_in_schema=False)
async def root(request: Request, response: Response):
    return RedirectResponse("https://account.devh.in/")


@app.post("/", include_in_schema=False)
async def root_post():
    return RedirectResponse("<script>window.location.href = '/';</script>")


def convert_to_pdf(mdc, title):
    from md2pdf.core import md2pdf
    
    md2pdf(
        pdf=f"temp/{title}.pdf",
        raw=mdc,
        css="font.css",
        
        extras=[
            "markdown.extensions.tables",
            "markdown.extensions.codehilite",
            "pymdownx.magiclink",
            "pymdownx.betterem",
            "pymdownx.superfences",
            "pymdownx.highlight",
            "pymdownx.snippets",
            "markdown.extensions.wikilinks",
            "markdown.extensions.toc",
            "pymdownx.arithmatex",
        ]
    )
    return f"temp/{title}.pdf"


async def delete_file(file_path: str, ):
    try:
        os.remove(file_path)
    except FileNotFoundError:
        pass  # If the file doesn't exist, ignore the error


@app.post("/sendpdf", include_in_schema=False)
async def send_pdf(request: Request, mdc=Form(...), title=Form(...)):
    file_name = convert_to_pdf(mdc, title)
    response = FileResponse(file_name, media_type="application/pdf", filename=file_name)
    return response

genai.configure(api_key="AIzaSyDhHXRkHjTYBUV9crg_EZ8E-XbuNyl1YQU")

# Set up the model
generation_config = {
    "temperature": 0.7,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 2048,
}

safety_settings = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_NONE",
    },
]

model = genai.GenerativeModel(
    model_name="gemini-1.0-pro",
    generation_config=generation_config,
    safety_settings=safety_settings,
)

class PromptData(BaseModel):
    new_prompt: str
    history: list = []

@app.post("/generate")
async def generate(data: PromptData):
    new_prompt = data.new_prompt
    history = data.history
    convo = model.start_chat(history=history)
    convo.send_message(new_prompt)
    response_text = convo.last.text

    # Return the response as JSON
    return JSONResponse({"response": response_text})


@app.get("/pull", include_in_schema=False)
async def pull():
    os.system("git pull")
    return {"message": "Pulled successfully!"}


