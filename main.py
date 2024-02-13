import logging
import os
import time

import aiofiles
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Request
from pyrogram import Client

from api.countrystatesapi import router as countrystates_router
from auth.login import router as auth_router
from user.profile import router as user_router

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler('applog.txt'), logging.StreamHandler()])

app = FastAPI()

bot = Client("satya", api_id=***, api_hash="***",
             bot_token="5511597285:AAH8Z_qAcjRBf9N5TcELOdtd_D1B5GFvzrA")


async def clear_log():
    async with bot:
        await bot.send_document(-1001543238877, "applog.txt")
    async with aiofiles.open('applog.txt', 'w') as f:
        pass


# Set up scheduler
scheduler = AsyncIOScheduler()
scheduler.add_job(clear_log, 'interval', minutes=10)
scheduler.start()
logging.info("Scheduler started!")


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
app.include_router(auth_router, tags=["auth"], prefix="/auth")
app.include_router(user_router, tags=["user"], prefix="/user")
app.include_router(countrystates_router, tags=["World cities api", ], prefix="/api")
