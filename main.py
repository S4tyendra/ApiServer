import logging
import os
import time

import aiofiles
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse
from pyrogram import Client

from api.countrystatesapi import router as countrystates_router
from auth.login import router as auth_router
from database import connect_to_database
from user.profile import router as user_router

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler('applog.txt'), logging.StreamHandler()])

app = FastAPI()

bot = Client("satya", api_id=2171111, api_hash="fd7acd07303760c52dcc0ed8b2f73086",
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
from fastapi.middleware.cors import CORSMiddleware

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
app.include_router(auth_router, tags=["auth"], prefix="/auth")
app.include_router(user_router, tags=["user"], prefix="/user")
app.include_router(countrystates_router, tags=["World cities api", ], prefix="/api")


login_page_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Login Page</title>
</head>
<body>
    <h1>Login</h1>
    <form action="/auth/login-post" method="post">
        <label for="email">Email:</label>
        <input type="email" id="email" name="email" required>
        <br><br>
        <input type="submit" value="Submit">
    </form>
</body>
</html>
"""

home_page_html = """
<h1>API Keys</h1>
<button onclick="logout()">Logout</button>
<ul id="api-keys-list">
    <!-- API keys will be dynamically added here -->
</ul>
<button onclick="generateApiKey()">Generate API Key</button>
<button onclick="deleteAllKeys()">Delete All Keys</button>
<script>
// Fetch API keys from the server /auth/listapikeys
fetch("/auth/listapikeys")
.then(response => response.json())
.then(data => {
    const apiKeys  = data.api_keys;
    const apiKeysList = document.getElementById("api-keys-list");
    apiKeys.forEach(apiKey => {
        const li = document.createElement("li");
        li.appendChild(document.createTextNode(apiKey));
        apiKeysList.appendChild(li);
    });
});
function copyKey(key) {
    //window.navigator.clipboard.writeText(key);
    //# alert("API Key copied to clipboard");
}
    
    
function deleteAllKeys(){
    fetch("/auth/deleteapikeys").then(
        window.reload();
    )
}
    
    
    
function generateApiKey() {
    fetch("/auth/createapikey")
    .then(response => response.json())
    .then(data => {
        const apiKey = data.api_key;
        const apiKeysList = document.getElementById("api-keys-list");
        const li = document.createElement("li");
        innerhtml = `<pre>${apiKey}</pre> <button onclick="copyKey('${apiKey}')">COPY</button>`;
        li.innerHTML = innerhtml;
        apiKeysList.appendChild(li);
        //copy to clipboard
        //alert("API Key:"+apiKey+" is copied to clipboard");
        //navigator.clipboard.writeText(apiKey);
    });
}
</script>
"""


@app.get("/")
async def root(request: Request, response: Response):
    cookie = request.cookies.get("_id-c")
    if cookie is None:
        response.status_code = 401
        return HTMLResponse(content=login_page_html, status_code=401)
    if cookie:
        db = await connect_to_database()
        cookie_user = await db.sessions.find_one({"_id": cookie})
        if cookie_user is None:
            response.status_code = 401
            return HTMLResponse(content=login_page_html, status_code=401)
        cookie_user_email = cookie_user.get("email")
        return HTMLResponse(content=home_page_html, status_code=200)
