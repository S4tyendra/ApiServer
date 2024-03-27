import secrets
from datetime import datetime

from fastapi import APIRouter, Form, HTTPException, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
from starlette.requests import Request

from database import connect_to_database
from functions.email_funcs import is_valid_email, send_otp
import html  # For HTML escaping
router = APIRouter()


class Email(BaseModel):
    email: str


class Verify(BaseModel):
    email: str
    otp: str


def generate_random_otp():
    import random
    return str(random.randint(100000, 999999))


@router.post("/login")
async def login(email: Email):
    if not is_valid_email(email.email, ["gmail.com", "iiitkota.ac.in", "devh.in", "satyendra.in"]):
        raise HTTPException(status_code=400, detail="Invalid email")
    db = await connect_to_database()
    user = await db.users.find_one({"email": email.email})
    if user is None:
        id = str(datetime.now().timestamp()).replace(".", "")
        otp = [{"otp": generate_random_otp(), "created_at": datetime.now().timestamp()}]
        await db.users.insert_one({"_id": id, "email": email.email, "otp": otp})
        send_otp(email.email, otp[0].get('otp'))
    else:
        otp: list = user["otp"]
        generated_otp = {"otp": generate_random_otp(
        ), "created_at": datetime.now().timestamp(), }
        otp.append(generated_otp)
        await db.users.update_one({"email": email.email}, {"$set": {"otp": otp}})
        send_otp(email.email, generated_otp.get('otp'))
    return {"message": "OTP sent"}


@router.post("/verify")
async def verify(response: Response, verify: Verify):
    db = await connect_to_database()
    user = await db.users.find_one({"email": verify.email})
    if user is None:
        raise HTTPException(status_code=400, detail="Invalid email")
    otps = user["otp"]
    otps.reverse()
    for i in range(len(otps)):
        if otps[i].get("otp") == verify.otp:
            if datetime.now().timestamp() - otps[i].get("created_at") > 300:
                raise HTTPException(status_code=400, detail="OTP expired")
            else:
                cookie = secrets.token_hex(32)
                await db.users.update_one({"email": verify.email}, {"$set": {"otp": []}})
                await db.sessions.insert_one(
                    {"_id": cookie, "email": verify.email, "created_at": datetime.now().timestamp()})
                response.set_cookie(key="_id-c", value=cookie, httponly=False, secure=False)
                return {"message": "OTP verified", "cookie": cookie}

    raise HTTPException(status_code=400, detail="Invalid OTP")


@router.get("/logout")
async def logout(response: Response, request: Request, all_sessions: bool = False):
    cookie = request.cookies.get("_id-c")
    if cookie is not None:
        if all_sessions:
            db = await connect_to_database()
            data = await db.sessions.find_one({"_id": cookie})
            await db.sessions.delete_many({"email": data.get("email")})
        else:
            db = await connect_to_database()
            await db.sessions.delete_one({"_id": cookie})
    response.delete_cookie(key="_id-c")
    return RedirectResponse(url="/")


@router.get("/createapikey")
async def create_api_key(request: Request):
    db = await connect_to_database()
    cookie = request.cookies.get("_id-c")
    if cookie is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    user = await db.sessions.find_one({"_id": cookie})
    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Count the number of existing API keys for the user
    api_keys_count = await db.sessions.count_documents({"email": user.get("email"), "type": "api_key"})
    if api_keys_count >= 10:
        raise HTTPException(status_code=400, detail="Maximum number of API keys reached")

    api_key = secrets.token_hex(32)
    await db.sessions.insert_one(
        {"_id": api_key, "email": user.get("email"), "created_at": datetime.now().timestamp(), "type": "api_key"})
    return {"api_key": api_key}


@router.get("/deleteapikeys")
async def delete_api_key(request: Request):
    db = await connect_to_database()
    cookie = request.cookies.get("_id-c")
    if cookie is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    cookie_user = await db.sessions.find_one({"_id": cookie})
    if cookie_user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    await db.sessions.delete_many({"email": cookie_user.get("email"), "type": "api_key"})
    return {"message": "All API keys deleted"}


@router.get("/listapikeys")
async def list_api_keys(request: Request):
    db = await connect_to_database()
    cookie = request.cookies.get("_id-c")
    if cookie is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    cookie_user = await db.sessions.find_one({"_id": cookie})
    if cookie_user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    email = cookie_user.get("email")
    api_keys_cursor = db.sessions.find({"email": email, "type": "api_key"})
    api_keys = []
    async for i in api_keys_cursor:
        api_keys.append(i["_id"][:4] + '*' * (len(i["_id"]) - 4))
    return {"api_keys": api_keys}


#
#
#
#
# Routes to handle events with HTML forms
#
#
#
#
#

submit_otp_html = """

<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>OTP Verification</title>
    <style>
    body {
    font-family: 'Arial', sans-serif;
    background-color: #2b2b2b;
    color: #fff;
    margin: 0;
    padding: 0;
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

input, button {
    width: 100%;
    padding: 10px;
    margin-bottom: 15px;
    box-sizing: border-box;
    border: 1px solid #ccc;
    border-radius: 5px;
    background-color: #444;
    color: #fff;
}

button {
    background-color: #4caf50;
    color: #fff;
    cursor: pointer;
}

button:hover {
    background-color: #45a049;
}

@media (max-width: 600px) {
    form {
        width: 90%;
    }
}
h1 {
    text-align: center;
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
</style>
</head>
<body>
    <h1>OTP Verification</h1>
    <form action="/auth/otp-verify" method="post">
        <p>Enter the OTP sent to your email</p>
        <label for="email">EMAIL:</label>
        <input type="email" id="email" name="email" value="${email}" readonly>
        <label for="otp">OTP:</label>
        <input type="text" id="otp" name="otp" required>
        <button type="submit">Submit</button>
    </form>
</body>
</html>
"""


@router.post("/login-post")
async def login_post(
        email: str = Form(...),
):
    if not is_valid_email(email, ["gmail.com",  "iiitkota.ac.in", "devh.in", "satyendra.in"]):
        raise HTTPException(status_code=400, detail="Invalid email, We dont accept these type of emails yet. please use gmail")
    db = await connect_to_database()
    user = await db.users.find_one({"email": email})
    if user is None:
        id = str(datetime.now().timestamp()).replace(".", "")
        otp = [{"otp": generate_random_otp(), "created_at": datetime.now().timestamp()}]
        await db.users.insert_one({"_id": id, "email": email, "otp": otp})
        send_otp(email, otp[0].get('otp'))
    else:
        otp: list = user["otp"]
        generated_otp = {"otp": generate_random_otp(
        ), "created_at": datetime.now().timestamp(), }
        otp.append(generated_otp)
        await db.users.update_one({"email": email}, {"$set": {"otp": otp}})
        send_otp(email, generated_otp.get('otp'))
    return HTMLResponse(content=submit_otp_html.replace("${email}", email), status_code=200)


@router.post("/otp-verify")
async def verify(response: Response, email: str = Form(...), otp: str = Form(...)):
    db = await connect_to_database()
    user = await db.users.find_one({"email": email})
    if user is None:
        raise HTTPException(status_code=400, detail="Invalid email")
    otps = user["otp"]
    otps.reverse()
    for i in range(len(otps)):
        if otps[i].get("otp") == otp:
            if datetime.now().timestamp() - otps[i].get("created_at") > 300:
                raise HTTPException(status_code=400, detail="OTP expired")
            else:
                cookie = secrets.token_hex(32)
                await db.users.update_one({"email": email}, {"$set": {"otp": []}})
                await db.sessions.insert_one(
                    {"_id": cookie, "email": email, "created_at": datetime.now().timestamp()})
                response = HTMLResponse(f"""<script>
                                        document.cookie = "_id-c={cookie}; domain=.devh.in; secure; httponly";
                                        window.location.href = '/';</script>""", status_code=200)
                response.set_cookie(key="_id-c", domain=".devh.in", value=cookie, httponly=False, secure=True)
                return response

    raise HTTPException(status_code=400, detail="Invalid OTP")


connect_to_3rd_party_html = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.tailwindcss.com?plugins=forms,typography,aspect-ratio,line-clamp"></script>
    <title>${app} X DEVH.IN</title>
</head>
<body>
<div class="
flex items-center justify-center min-h-screen bg-background-foreground
">
    <div class="rounded-lg text-card-foreground w-full max-w-md mx-auto bg-white border border-gray-200 shadow-sm"
         data-v0-t="card">
        <div class="space-y-1.5 flex flex-col items-center p-6">
            <div class="space-y-2 text-center"><h1 class="text-2xl font-bold">Connection Request</h1>
                <p class="text-sm text-gray-500">
                    ${app} is requesting access to your account.
                </p>
                <sub>
                    ${app_info}
                </sub>
            </div>
        </div>
        <div class="flex flex-col p-6 gap-4">
            <div class="flex items-center gap-4"><svg xmlns="http://www.w3.org/2000/svg" width="2em" height="2em" viewBox="0 0 24 24">  <path fill="currentColor" d="M12 12h7c-.53 4.11-3.28 7.78-7 8.92zH5V6.3l7-3.11M12 1L3 5v6c0 5.55 3.84 10.73 9 12c5.16-1.27 9-6.45 9-12V5z" /> </svg>
                <div class="grid gap-1.5"><h3 class="text-base font-semibold"><b>Access Everything of your account</b></h3>
                    <p class="text-sm text-gray-500">
                        This application will be granted access to manage your account.
                    </p></div>
            </div>
<!--            <div class="flex items-center gap-4"><img src="/placeholder.svg" width="64" height="64" alt="App Icon"-->
<!--                                                      class="rounded-md border"-->
<!--                                                      style="aspect-ratio:64/64;object-fit:cover">-->
<!--                <div class="grid gap-1.5"><h3 class="text-base font-semibold">Access your email address</h3>-->
<!--                    <p class="text-sm text-gray-500">-->
<!--                        This application will be able to access your email address.-->
<!--                    </p></div>-->
<!--            </div>-->
        </div>
        <div class="items-center flex p-6 border-t justify-end">
            <a href="/">
            <button class="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border hover:text-accent-foreground h-10 px-4 py-2 mr-2.5 bg-white border-gray-200 text-gray-900 shadow-sm hover:bg-gray-50">
                Deny
            </button>
                </a>
            <form method="post">
            <button
                    class="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-10 px-4 py-2 bg-gray-900 text-gray-50 shadow hover:bg-gray-900/90">
                Allow
            </button>
                </form>
        </div>
        <div class="p-4 text-sm text-gray-500">
            Your data is handled securely. We respect your privacy.
        </div>
    </div>
</div>
</body>
</html>


"""


@router.get("/connect")
async def connect(request: Request, app: str, _hash: str, state: str):
    apps = ['telegram@devh.in?app=telegram']
    if app not in apps:
        return RedirectResponse(url="/auth/connectionerror?error=Invalid app")
    cookie = request.cookies.get("_id-c")
    if cookie is None:
        return RedirectResponse(url="/")
    return HTMLResponse(content=connect_to_3rd_party_html.replace("${app}", "<b>Intelligent</b>").replace("${app_info}","<b>Intelligent </b><sup> devh.in</sup> Is an official bot from devh.in"), status_code=200)


@router.post("/connect")
async def connect_post(request: Request, app: str, _hash: str, state: str):
    apps = ['telegram@devh.in?app=telegram']
    if app not in apps:
        return RedirectResponse(url="/auth/connectionerror?error=Invalid app")
    cookie = request.cookies.get("_id-c")
    if cookie is None:
        return RedirectResponse(url="/")
    db = await connect_to_database()
    user = await db.sessions.find_one({"_id": cookie})
    if user is None:
        return RedirectResponse(url="/")
    email = user.get("email")
    new_cookie = secrets.token_hex(32)
    await db.users.update_one({"email": email}, {"$set": {"otp": []}})
    try:

        v = await db.tg_sessions.update_one(
            {"_hash": _hash, "state": state}, {
                "$set": {"cookie": new_cookie, "email": email, "created_at": datetime.now().timestamp()},
                "$unset": {"_hash": "", "state": ""}
            })
        print(v)
        await db.sessions.insert_one(
            {"_id": new_cookie, "email": email, "created_at": datetime.now().timestamp()})
        return RedirectResponse(url="/auth/connectionsuccess?app=telegram")
    except:
        return RedirectResponse(url="/auth/connectionerror?error=Error occured")


@router.get("/connectionerror")
async def connection_error(request: Request, error: str):
    escaped_error = html.escape(error)  # Escape potential HTML characters
    return HTMLResponse(content=f"<code><h1>{escaped_error}</h1></code>", status_code=400)
@router.post("/connectionerror")
async def connection_error_post(request: Request, error: str):
    escaped_error = html.escape(error)  # Escape potential HTML characters
    return HTMLResponse(content=f"<code><h1>{escaped_error}</h1></code>", status_code=400)

@router.get("/connectionsuccess")
async def connection_success(request: Request, app: str):
    if app == "telegram":
        return HTMLResponse(content="""<code><h1>Connected to Intelligent</h1></code><script>setTimeout(function() {
        // Redirect to the specified URL
        window.location.href = 'https://t.me/iSatyaBot';
      }, 3000); </script>""", status_code=200)
    else:
        return RedirectResponse(url="/auth/connectionerror?error=Invalid app")

@router.post("/connectionsuccess")
async def connection_success(request: Request, app: str):
    if app == "telegram":
        return HTMLResponse(content="""<code><h1>Connected to Intelligent</h1></code><script>setTimeout(function() {
        // Redirect to the specified URL
        window.location.href = 'https://t.me/iSatyaBot';
      }, 3000); </script>""", status_code=200)
    else:
        return RedirectResponse(url="/auth/connectionerror?error=Invalid app")
