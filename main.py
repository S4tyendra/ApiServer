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



login_page_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Login | API AUTH devh</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
    body {
    font-family: 'Arial', sans-serif;
    background-color: #2b2b2b;
    color: #fff;
    margin: 0;
    padding: 0;
}

h1 {
    text-align: center;
}

form {
    max-width: 400px;
    margin: 0 auto;
    margin-top:10%;
    background-color: #333;
    padding: 20px;
    border-radius: 10px;
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.2);
}

label {
    display: block;
    margin-bottom: 8px;
}

input {
    width: 100%;
    padding: 10px;
    margin-bottom: 15px;
    box-sizing: border-box;
    border: 1px solid #ccc;
    border-radius: 5px;
    background-color: #444;
    color: #fff;
}

p {
    width: 100%;
    padding: 10px;
    margin-bottom: 15px;
    box-sizing: border-box;
    border: 1px solid #ccc;
    border-radius: 5px;
    background-color: #444;
    color: #fff;
}

input[type="submit"] {
    background-color: #4caf50;
    color: #fff;
    cursor: pointer;
}

input[type="submit"]:hover {
    background-color: #45a049;
}

@media (max-width: 600px) {
    form {
        width: 90%;
    }
}

    </style>
</head>
<body>
    <h1>Login</h1>
    <form action="/auth/login-post" method="post">
    <p>We will create one account for you, if it doesnt exist!</p>
        <label for="email">Email:</label>
        <input type="email" placeholder="Enter your email here" id="email" name="email" required>
        <br><br>
        <input type="submit" value="Submit">
    </form>
</body>
</html>
"""

home_page_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API Keys</title>
    <style>
        body {
            font-family: 'Arial', sans-serif;
            background-color: #2b2b2b;
            color: #fff;
            margin: 0;
            padding: 0;
        }

        h1 {
            text-align: center;
        }

        button {
            padding: 10px;
            margin: 10px;
            box-sizing: border-box;
            border: none;
            border-radius: 5px;
            background-color: #4caf50;
            color: #fff;
            cursor: pointer;
        }

        button:hover {
            background-color: #45a049;
        }

        ul {
            list-style-type: none;
            padding: 0;
        }

        li {
            margin-bottom: 10px;
            overflow: scroll;
            padding:3px;
            margin: 3px;
            border-radius: 5px;
            background-color: #444;
            border: 1px solid #ccc;
        }

        code {
            background-color: #333;
            padding: 5px;
            border-radius: 5px;
            display: block;
            overflow: scroll;
        }

        pre {
            margin: 0;
        }

        sub {
            color: #888;
            display: block;
            margin-top: 5px;
        }
        .card {
            margin: 30px;
            background-color: #333;
            padding:30px;
            overflow: hidden;
        }
        .login-email{
            text-align: center;
            margin-top: 10px;
        }
        i{
            color: #4caf50;
        }
    </style>
</head>
<body>
    <h1 id="api-keys">API Keys</h1>
    <button onclick="logout()">Logout</button>
    <div class = "card">
    <p class="infooo"></p>
    <ul id="api-keys-list">
        <!-- API keys will be dynamically added here -->
    </ul>
    </div>
    <button onclick="generateApiKey()">Generate API Key</button>
    <button onclick="deleteAllKeys()">Delete All Keys</button>
    <button onclick="window.location.href = '/docs';">Docs</button>
    <script>
        const apikeys = document.getElementById("api-keys");
        apikeys.innerHTML = "Loading...";

        // Fetch API keys from the server /auth/listapikeys
        fetch("/auth/listapikeys")
            .then(response => response.json())
            .then(data => {
                const apiKeys = data.api_keys;
                if (apiKeys.length === 0) {
                    const infooO = document.querySelector(".infooo");
                    infooO.innerHTML = "No API keys found. Click 'Generate API Key' to create one.";
                }
                const apiKeysList = document.getElementById("api-keys-list");
                apiKeysList.innerHTML = ""; // Clear existing list
                apiKeys.forEach(apiKey => {
                    const li = document.createElement("li");
                    li.innerHTML = `<code><pre>${apiKey}</pre></code>`;
                    apiKeysList.appendChild(li);
                });
                apikeys.innerHTML = "API Keys";
            });

        function copyKey(key) {
            // window.navigator.clipboard.writeText(key);
            // alert("API Key copied to clipboard");
        }

        function deleteAllKeys() {
            fetch("/auth/deleteapikeys").then(resp => window.location.reload());
        }

        function generateApiKey() {
            fetch("/auth/createapikey")
                .then(response => response.json())
                .then(data => {
                    const apiKey = data.api_key;
                    if  (data.detail) {
                    alert(data.detail);
                    return;
                }
                    const apiKeysList = document.getElementById("api-keys-list");
                    const li = document.createElement("li");
                    li.innerHTML = `<code><pre>${apiKey}</pre></code> <sub>COPY it now, you won't be able to see it later</sub>`;
                    apiKeysList.appendChild(li);
                    const infooO = document.querySelector(".infooo");
                    infooO.innerHTML = "";
                });
        }

        function logout() {
            fetch("/auth/logout").then(resp => window.location.reload());
        }
    </script>
    <footer>
    <p class="login-email">Logged in as: <i>${email}</i></p>
    </footer>
</body>
</html>

"""


@app.get("/", include_in_schema=False)
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
        return HTMLResponse(content=home_page_html.replace("${email}", cookie_user_email), status_code=200)


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


async def delete_file(file_path: str):
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
