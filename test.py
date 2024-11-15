# --- Config and Requirements ---
from fastapi import FastAPI, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorClient
import webauthn
from starlette.responses import HTMLResponse
from webauthn.helpers import bytes_to_base64url
from webauthn.helpers.structs import (
    RegistrationCredential,
    AuthenticationCredential,
    UserVerificationRequirement, AuthenticatorSelectionCriteria, ResidentKeyRequirement, AttestationConveyancePreference
)
from pydantic import BaseModel, Field
from typing import Optional, List
import uuid
from datetime import datetime, timedelta
import jwt
from bson import ObjectId
import os
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
JWT_SECRET = os.getenv("JWT_SECRET")
RP_ID = os.getenv("RP_ID", "account.devh.in")  # Your domain
RP_NAME = os.getenv("RP_NAME", "DevH")
ORIGIN = os.getenv("ORIGIN", "https://account.devh.in")  # Your origin URL


# --- Database Setup ---
class MongoDB:
    client: AsyncIOMotorClient = None
    db = None

    @classmethod
    async def connect_db(cls):
        cls.client = AsyncIOMotorClient(MONGODB_URL)
        cls.db = cls.client.passkeys_db

    @classmethod
    async def close_db(cls):
        if cls.client:
            await cls.client.close()

    @classmethod
    def get_db(cls):
        return cls.db


# --- Pydantic Models ---
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)


class User(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    username: str
    email: Optional[str]
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class Credential(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    credential_id: str
    public_key: bytes
    sign_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, bytes: lambda v: bytes_to_base64url(v)}


class Challenge(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    challenge: str
    user_id: Optional[str]
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


# --- Request/Response Models ---
class RegistrationRequest(BaseModel):
    username: str
    email: Optional[str] = None


class AuthenticationRequest(BaseModel):
    credential_id: str


# --- FastAPI App ---
app = FastAPI()


# --- Startup and Shutdown ---
@app.on_event("startup")
async def startup():
    await MongoDB.connect_db()


@app.on_event("shutdown")
async def shutdown():
    await MongoDB.close_db()


# --- Helper Functions ---
async def get_user_by_username(username: str):
    """Get user by username from MongoDB"""
    db = MongoDB.get_db()
    return await db.users.find_one({"username": username})


async def store_challenge(challenge: str, user_id: Optional[str] = None):
    """Store challenge in MongoDB"""
    db = MongoDB.get_db()
    expires_at = datetime.utcnow() + timedelta(minutes=5)
    challenge_doc = Challenge(
        challenge=challenge,
        user_id=user_id,
        expires_at=expires_at
    ).dict(by_alias=True)
    await db.challenges.insert_one(challenge_doc)


async def get_challenge(user_id: Optional[str] = None):
    """Get latest valid challenge from MongoDB"""
    db = MongoDB.get_db()
    query = {
        "expires_at": {"$gt": datetime.utcnow()}
    }
    if user_id:
        query["user_id"] = user_id
    challenge = await db.challenges.find_one(
        query,
        sort=[("created_at", -1)]
    )
    if not challenge:
        raise HTTPException(status_code=400, detail="Challenge not found or expired")
    return challenge


# --- Registration Endpoints ---
@app.post("/auth/register/begin")
async def start_registration(request: RegistrationRequest):
    """Start passkey registration process"""
    try:
        # Check if user exists
        if await get_user_by_username(request.username):
            raise HTTPException(status_code=400, detail="Username already exists")

        user_id = str(uuid.uuid4())

        # Generate registration options
        # r_key : ResidentKeyRequirement = ResidentKeyRequirement()
        aut_se : AuthenticatorSelectionCriteria = AuthenticatorSelectionCriteria(
            user_verification=UserVerificationRequirement.REQUIRED,
            resident_key=ResidentKeyRequirement.REQUIRED
        )
        options = webauthn.generate_registration_options(
            rp_id=RP_ID,
            rp_name=RP_NAME,
            user_id=user_id.encode("utf-8"),
            user_name=request.username,
            authenticator_selection=aut_se,
            attestation=AttestationConveyancePreference.NONE
        )

        # Store challenge
        await store_challenge(
            challenge=bytes_to_base64url(options.challenge),
            user_id=user_id
        )

        return options

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/auth/register/complete")
async def complete_registration(credential: RegistrationCredential):
    """Complete passkey registration"""
    try:
        db = MongoDB.get_db()

        # Get stored challenge
        challenge_doc = await get_challenge(credential.response.client_data.user_id)

        # Verify registration
        verification = webauthn.verify_registration_response(
            credential=credential,
            expected_challenge=webauthn.base64url_to_bytes(challenge_doc["challenge"]),
            expected_origin=ORIGIN,
            expected_rp_id=RP_ID
        )

        # Store user
        user = User(
            _id=ObjectId(),
            id=verification.user_id,
            username=credential.response.client_data.user_name
        )
        await db.users.insert_one(user.dict(by_alias=True))

        # Store credential
        cred = Credential(
            user_id=verification.user_id,
            credential_id=bytes_to_base64url(verification.credential_id),
            public_key=verification.credential_public_key,
            sign_count=verification.sign_count
        )
        await db.credentials.insert_one(cred.dict(by_alias=True))

        return {"status": "success"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- Authentication Endpoints ---
@app.post("/auth/login/begin")
async def start_authentication():
    """Start passkey authentication"""
    try:
        # Generate authentication options
        options = webauthn.generate_authentication_options(
            rp_id=RP_ID,
            user_verification=UserVerificationRequirement.REQUIRED,
        )

        # Store challenge
        await store_challenge(bytes_to_base64url(options.challenge))

        return options

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/auth/login/complete")
async def complete_authentication(credential: AuthenticationCredential):
    """Complete passkey authentication"""
    try:
        db = MongoDB.get_db()

        # Get stored challenge
        challenge_doc = await get_challenge()

        # Get credential from database
        stored_credential = await db.credentials.find_one({
            "credential_id": bytes_to_base64url(credential.raw_id)
        })
        if not stored_credential:
            raise HTTPException(status_code=400, detail="Credential not found")

        # Verify authentication
        verification = webauthn.verify_authentication_response(
            credential=credential,
            expected_challenge=webauthn.base64url_to_bytes(challenge_doc["challenge"]),
            expected_origin=ORIGIN,
            expected_rp_id=RP_ID,
            credential_public_key=stored_credential["public_key"],
            credential_current_sign_count=stored_credential["sign_count"]
        )

        # Update sign count
        await db.credentials.update_one(
            {"_id": stored_credential["_id"]},
            {"$set": {"sign_count": verification.new_sign_count}}
        )

        # Generate JWT token
        token = jwt.encode(
            {
                "user_id": stored_credential["user_id"],
                "exp": datetime.utcnow() + timedelta(days=1)
            },
            JWT_SECRET,
            algorithm="HS256"
        )

        return {"access_token": token, "token_type": "bearer"}

    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


# --- Middleware for cleaning up expired challenges ---
@app.middleware("http")
async def cleanup_expired_challenges(request, call_next):
    """Cleanup expired challenges periodically"""
    db = MongoDB.get_db()
    await db.challenges.delete_many({
        "expires_at": {"$lt": datetime.utcnow()}
    })
    response = await call_next(request)
    return response

@app.get("/")
async def read_root():
    return HTMLResponse(
        r"""
<form id="registerForm">
  <input type="text" id="username" placeholder="Username" required>
  <input type="email" id="email" placeholder="Email">
  <button type="button" onclick="register()">Register</button>
</form>


<script>
async function register() {
  const username = document.getElementById('username').value;
  const email = document.getElementById('email').value;

  try {
    // 1. Get options from server
    const response = await fetch('/auth/register/begin', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, email }),
    });
    const options = await response.json();


    // 2. Create credentials
    const credential = await navigator.credentials.create({
      publicKey: options,
    });

    // 3. Send credential back to server
    await fetch('/auth/register/complete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credential), // Send the entire credential object
    });

    alert('Registration successful!');

  } catch (error) {
    console.error('Registration error:', error);
    alert('Registration failed. Please try again.');
  }
}

</script>
<script>
// Add event listener to form submit to prevent page reload
document.getElementById('registerForm').addEventListener('submit', function(event) {
  event.preventDefault(); // Prevent form from submitting normally
  register(); // Call your register function
});
</script>
        """
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)