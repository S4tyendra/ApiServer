from fastapi.middleware.cors import CORSMiddleware
import logging
import os
import time

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Form, Request, Response
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from fastapi import FastAPI, Request
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from api.countrystatesapi import router as countrystates_router
# from auth.login import router as auth_router
from database import connect_to_database
from user.profile import router as user_router
from stripe_pay.payments import app as stripe_router
from auth.google import router as google_router
from iiitkres import router as iiitkres_router
from storage import router as drive_router
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

app.include_router(user_router, tags=["user"], prefix="/user")
app.include_router(countrystates_router, tags=[
    "World cities api", ], prefix="/api")
app.include_router(stripe_router, tags=["stripe"], prefix="/stripe", include_in_schema=False)
app.include_router(google_router, tags=["GAUTH"], prefix="/auth", include_in_schema=False)
app.include_router(iiitkres_router, tags=["IIITK RES"], prefix="/iiitk")
app.include_router(drive_router, tags=["Storage"], prefix="/storage")


@app.get("/", include_in_schema=False)
async def root(request: Request, response: Response):
    return RedirectResponse("https://account.devh.in/")




async def delete_file(file_path: str, ):
    try:
        os.remove(file_path)
    except FileNotFoundError:
        pass 




@app.get("/pull", include_in_schema=False)
async def pull():
    os.system("git pull")
    return {"message": "Pulled successfully!"}


