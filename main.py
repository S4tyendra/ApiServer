import logging
import os
import time

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Request
from fastapi import Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from api.countrystatesapi import router as countrystates_router
from auth.google import router as google_router
from iiitkres import router as iiitkres_router
from storage import router as drive_router
from stripe_pay.payments import router as stripe_router
from auth.login import router as auth_router
from user.profile import router as user_router

#Print python version


# os.system("git pull ")

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler('app.log'), logging.StreamHandler()])

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
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import pytz
import time
import logging

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ist = pytz.timezone('Asia/Kolkata')

@app.middleware("http")
async def log_request(request: Request, call_next):
    start_time = time.time()
    
    # Get the client IP address
    client_ip = request.headers.get("CF-Connecting-IP") or request.client.host
    
    if any(key in request.headers for key in ["X-API-KEY", "WEB-KEY", "x-api-key", "web-key"]):
        from database import connect_to_database
        db = await connect_to_database()
        token = next((request.headers.get(key) for key in ["X-API-KEY", "WEB-KEY", "x-api-key", "web-key"] if key in request.headers), None)
        try:
            current_time_ist = datetime.now(ist)
            await db.sessions.update_one({"_id": token}, {"$set": {"last_accessed": current_time_ist}})
        except Exception as e:
            logging.error(f"Error updating session: {e}")

    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}"
    
    logging.info(
        f"{request.method} - {request.url} - IP: {client_ip} - "
        f"Cookie: {request.headers.get('cookie')} - "
        f"API Key: {request.headers.get('x-api-key')} - "
        f"Process Time: {process_time:.4f}s"
    )
    
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
app.include_router(auth_router, tags=["Auth"], prefix="/auth")


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


@app.get("/set")
async def set_file_content(file:str):
    with open("list.txt", 'a') as f:
        f.write(f"{file}\n")
    return {"message": "Added successfully!"}
@app.get("/get")
async def get_file_contents_as_list():
    with open("list.txt", 'r') as f:
        v = f.readlines()
    return v

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", reload=True, port=8000)
