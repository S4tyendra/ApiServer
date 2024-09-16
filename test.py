import os
import json
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
import google.generativeai as genai
import oauthlib
from google.auth.transport.requests import Request
import requests

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

SCOPES = [
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    # 'https://www.googleapis.com/auth/generative-language.tuning',
    "https://www.googleapis.com/auth/generative-language.retriever",
    "openid",
]

USER_DATA_FILE = "user_data.json"


def load_user_data():
    if os.path.exists(USER_DATA_FILE):
        try:
            with open(USER_DATA_FILE, "r") as f:
                content = f.read().strip()
                if content:
                    return json.loads(content)
                else:
                    print("User data file is empty. Starting with no users.")
                    return {}
        except json.JSONDecodeError:
            print("Error reading user data file. Starting with no users.")
            return {}
    return {}


def save_user_data(user_data):
    with open(USER_DATA_FILE, "w") as f:
        json.dump(user_data, f, indent=2)


def get_user_info(creds):
    try:
        userinfo_endpoint = "https://www.googleapis.com/oauth2/v3/userinfo"
        response = requests.get(
            userinfo_endpoint, headers={"Authorization": f"Bearer {creds.token}"}
        )
        if response.status_code == 200:
            user_info = response.json()
            return user_info.get("email"), user_info.get("name", "Unknown")
        else:
            print(f"Failed to fetch user info. Status code: {response.status_code}")
            return None, None
    except Exception as e:
        print(f"Error fetching user info: {str(e)}")
        return None, None


def authenticate(user_id):
    user_data = load_user_data()
    creds = None

    if user_id in user_data and "token" in user_data[user_id]:
        token_data = user_data[user_id]["token"]
        creds = Credentials.from_authorized_user_info(token_data, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = Flow.from_client_secrets_file(
                "client_secret_708674027164-39pdc4ibg9pllt1npvg5f2oc3p00t67r.apps.googleusercontent.com.json",
                SCOPES,
            )

            flow.redirect_uri = "http://localhost:4000/callback"
            auth_url, _ = flow.authorization_url(prompt="consent")

            print(f"Please visit this URL to authorize the application: {auth_url}")
            print(
                "After granting permission, you will be redirected to a URL starting with 'http://localhost:4000'."
            )
            print("Copy the entire URL and paste it here:")

            callback_url = input().strip()

            try:
                flow.fetch_token(authorization_response=callback_url)
            except oauthlib.oauth2.rfc6749.errors.InsecureTransportError:
                from urllib.parse import urlparse, parse_qs

                query = urlparse(callback_url).query
                code = parse_qs(query)["code"][0]
                flow.fetch_token(code=code)

            creds = flow.credentials

        # Fetch user info
        email, name = get_user_info(creds)
        if email:
            user_data[user_id] = {
                "email": email,
                "name": name,
                "token": {
                    "token": creds.token,
                    "refresh_token": creds.refresh_token,
                    "token_uri": creds.token_uri,
                    "client_id": creds.client_id,
                    "client_secret": creds.client_secret,
                    "scopes": creds.scopes,
                },
            }
            save_user_data(user_data)
        else:
            print("Warning: Could not fetch user info. User data might be incomplete.")

    return creds


def generate_content(creds):
    genai.configure(credentials=creds)
    model = genai.GenerativeModel("gemini-1.5-pro")
    response = model.generate_content(
        "Tell me a short story about a robot learning to paint."
    )
    print(response.text)


def main():
    user_data = load_user_data()

    if not user_data:
        print("No users found. Let's add a new user.")
        user_id = input("Enter a unique user ID: ")
    else:
        print("Existing users:")
        for uid, data in user_data.items():
            print(f"User ID: {uid}, Name: {data['name']}, Email: {data['email']}")
        user_id = input("Enter a user ID to authenticate (or a new ID to add a user): ")

    creds = authenticate(user_id)
    generate_content(creds)


if __name__ == "__main__":
    main()
